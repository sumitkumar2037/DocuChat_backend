from fastapi import FastAPI,File,UploadFile, Form, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
from dotenv import load_dotenv
import shutil
from src.modelCall import query_retrival
from src.chat import save_chat_in_redis,load_chat_from_redis,primary_chain,fallback_chain
from langchain.messages import AIMessage
import uuid
from datetime import datetime, timedelta
import jwt 
from src.session.jwt_verify import create_guest_jwt,verify_jwt
from src.session.session_management import cleanup_guest_session
import logging
import aiofiles
from src.model import load_files_from_folder,embed_chunk_to_pinecone,get_loader
from src.classifer.classifier_tool import take_user_query
from src.tool.document_rag import route_dacument_rag
from src.tool.general_llm import route_general_llm
from src.tool.web_search import route_web_search
import  asyncio
from src.store.classifier_context import save_metadata_from_doc,save_summary
from src.store.redis_config import redis_client
from fastapi import BackgroundTasks
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
    background_tasks:BackgroundTasks,
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
    file_path = os.path.join(guest_id_dir, file.filename)

    async with aiofiles.open(file_path,'wb') as buffer_chunk:
        chunk=await file.read(1024*1024)
        while chunk:
            await buffer_chunk.write(chunk)
            chunk=await file.read(1024*1024)
    redis_client.set(f'status:{guest_id}','unknown')
    background_tasks.add_task(
        process_document,
        guest_id,
        file_path,
        file.filename,
        file.content_type
    )
    

    #create a jwt token :
    token = create_guest_jwt(guest_id)

    # Return token to frontend
    return {
        "message": "File uploaded successfully",
        "token": token,
        "expires_in": 5 * 60,
        'status':'processing'
    }



@app.post("/chat")
async def chat(
    query:str=Form(...),
    guest_id:str=Depends(verify_jwt)
):
    #taking user query into agentic route 
    route_result=take_user_query(query,guest_id)
    final_result=""
    if route_result=='DOCUMENT_RAG':
        final_result=await route_dacument_rag(query,guest_id)
    if route_result=='WEB_SEARCH':
        final_result=await route_web_search(query,guest_id)
    if route_result=='GENERAL_LLM':
        final_result= await route_general_llm(query,guest_id)
    logger.info(f'final_result:{final_result}')
    if final_result is None:
        final_result="no answer from llm"
    ai_message=AIMessage(final_result).content
    save_chat_in_redis(guest_id,'assitant',ai_message)
    return {'ai_message':ai_message}
    
        
    
         
@app.post('/logout')
async def exit(token:str=Depends(verify_jwt)):
    try:
        cleanup_guest_session(token)
    except Exception as e:
        raise HTTPException(status_code=401,detail='something went wrong')
    return {'status_code':200 , 'detail':"deletion of user session successfully"}
    
@app.get("/status")
def check_status(token:str=Depends(verify_jwt)):
    return {
        "status": redis_client.get(f'status:{token}')
    }


def process_document(guest_id: str, file_path: str, filename: str, content_type: str):
    try:
        redis_client.set(f'status:{guest_id}',"processing")

        # 1. Load document (blocking)
        loader = get_loader(file_path)
        docs = loader.load()

        # Attach metadata
        for d in docs:
            d.metadata["guest_id"] = guest_id
            d.metadata["source"] = file_path

        embed_chunk_to_pinecone(guest_id, docs)
        file_metadata = {
            "guest_id": guest_id,
            "filename": filename,
            "content_type": content_type,
            "total_pages": len(docs),
            "file_path": file_path,
        }
        save_metadata_from_doc(guest_id, file_metadata)
        short_summary = docs[0].page_content[:1500]

        save_summary(short_summary, guest_id)
        redis_client.set(f'status:{guest_id}',"completed")

    except Exception as e:
        redis_client.set(f'status:{guest_id}',"failed")
        print("Embedding Error:", e)



    

