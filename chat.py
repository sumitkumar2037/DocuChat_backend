from modelCall import query_retrival
from langchain.messages import HumanMessage,AIMessage,SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
import redis
import json
import os
from langchain_openai import ChatOpenAI
#----------------------------------------------
#.       Redis Implemetation
#----------------------------------------------

#load the api key 
load_dotenv()

# prompt 
template=ChatPromptTemplate.from_messages([
    ("system","You are a helpful assistant. "
     "Use ONLY the context below to answer the user query , refine the answer and present in user friendly words.\n\n"
     "Context:\n{context}"),
    MessagesPlaceholder(variable_name='chat_history'),
    ('human','{query}')
    ]
)
#local
redis_client=redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

#production
# REDIS_URL = os.getenv("REDIS_URL")

# redis_client = redis.from_url(
#     REDIS_URL,
#     decode_responses=True
# )
def save_chat_in_redis(guest_id:str,role:str,content:str)->None:
    key=f"chat:{guest_id}"
    redis_client.rpush(
        key,
        json.dumps({"role":role,"content":content})
    )
    

def load_chat_from_redis(guest_id:str,limit=6)->list:
    stored_msg=redis_client.lrange(guest_id,-limit,-1)
    messages=[]
    for msg in stored_msg:
        m=json.loads(msg)
        if m['role']=='user':
            messages.append(HumanMessage(m['content']))
        else:
            messages.append(AIMessage(m['content']))
    return messages

# send this prompt to llm 
model=ChatGoogleGenerativeAI(model="gemini-2.5-flash")
model2=ChatOpenAI(model="nvidia/nemotron-3-nano-30b-a3b:free",base_url="https://openrouter.ai/api/v1")

parser=StrOutputParser()
primary_chain=template | model | parser
fallback_chain=template | model2 | parser
#initalize the chain 
#create session
# while True:
#     query=str(input('>>>you'))
#     save_chat_in_redis(session,'user',query)
#     if query=='exit':
#         break
#     chat_history=load_chat_from_redis(session)
#     chain=template | model | parser
#     context=query_retrival(query)
#     result=chain.invoke({'chat_history':chat_history,'context':context,'query':query})
#     print(AIMessage(result).content)
#     save_chat_in_redis(session,'AI',result)




