from fastapi import FastAPI,File,UploadFile, Form, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
from dotenv import load_dotenv
import shutil
from modelCall import query_retrival
from chat import save_chat_in_redis,load_chat_from_redis,primary_chain,fallback_chain
from langchain.messages import AIMessage
import uuid
from datetime import datetime, timedelta
import jwt
from jwt_verify import create_guest_jwt,verify_jwt
from session_management import cleanup_guest_session
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

logger = logging.getLogger(__name__)

#load the api key 
load_dotenv()

app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://docu-chat-frontend-phi.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

#directory path to save file
BASE_UPLOAD_DIR = "items"
os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/upload")
async def upload_file(
    
    file: UploadFile = File(...)
):
    # Validate file type
    allowed_types = ["application/pdf", "text/plain"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Create uuid-specific folder
    guest_id=str(uuid.uuid4())
    guest_id_dir = os.path.join(BASE_UPLOAD_DIR, guest_id)
    os.makedirs(guest_id_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(guest_id_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    #create a jwt token :
    token = create_guest_jwt(guest_id)

    # Return token to frontend
    return {
        "message": "File uploaded successfully",
        "token": token,
        "expires_in": 5 * 60
    }

@app.post("/chat")
async def chat(
    query:str=Form(...),
    guest_id:str=Depends(verify_jwt)
):
     
    
    save_chat_in_redis(guest_id,'user',query)
    chat_history=load_chat_from_redis(guest_id,10)
    logger.info('current chat history :',chat_history)
    context=query_retrival(query,guest_id)
    result=""
    try:
        result = primary_chain.invoke({
        "chat_history": chat_history,
        "context": context,
        "query": query
    })
    except Exception as primary_error:
        print("Primary LLM failed:", primary_error)
        try:
            result = fallback_chain.invoke({
                "chat_history": chat_history,
                "context": context,
                "query": query
            })
        except Exception as fallback_error:
             logger.info("Fallback LLM failed:", fallback_error)

        return {
            "ai_message": "AI services are currently unavailable."
        }

    ai_message=AIMessage(result).content
    save_chat_in_redis(guest_id,'assitant',ai_message)
    logger.info('final chat history :',chat_history)
    return {'ai_message':ai_message}
    
        
    
         
@app.post('/logout')
async def exit(token:str=Depends(verify_jwt)):
    try:
        cleanup_guest_session(token)
    except Exception as e:
        raise HTTPException(status_code=401,detail='something went wrong')
    return {'status_code':200 , 'detail':"deletion of user session successfully"}
    





    

