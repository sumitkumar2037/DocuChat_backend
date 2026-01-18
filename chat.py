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
template = ChatPromptTemplate.from_messages([
    ("system", 
     "You are an intelligent document assistant. Your purpose is to help users understand their documents by answering questions accurately.\n\n"
     " CORE PRINCIPLES:\n"
     "• Answer EXCLUSIVELY based on the context provided below\n"
     "• Be accurate, clear, and helpful\n"
     "• Admit when information is not available in the documents\n"
     "• Never fabricate or assume information\n\n"
     " WHEN INFORMATION IS AVAILABLE:\n"
     "• Provide a direct, comprehensive answer\n"
     "• Structure your response clearly\n"
     "• Reference specific sections when helpful\n"
     "• Use natural, user-friendly language\n\n"
     " WHEN INFORMATION IS NOT AVAILABLE:\n"
     "Respond with: \"I couldn't find information about that in the provided documents. The available content covers [briefly mention what topics are in context]. Is there something else from the document I can help you with?\"\n\n"
     " CONTEXT FROM DOCUMENTS:\n"
     "{context}\n\n"
     "---\n"
     "Now, answer the user's question based solely on the above context."
    ),
    MessagesPlaceholder(variable_name='chat_history'),
    ('human', '{query}')
])
#local
# redis_client=redis.Redis(
#     host="localhost",
#     port=6379,
#     decode_responses=True
# )

#production
REDIS_URL = os.getenv("REDIS_URL")

redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True
)
def save_chat_in_redis(guest_id:str,role:str,content:str)->None:
    key=f"chat:{guest_id}"
    redis_client.rpush(
        key,
        json.dumps({"role":role,"content":content})
    )
    print('saved chat in redis instance')
    

def load_chat_from_redis(guest_id:str,limit=6)->list:
    key = f"chat:{guest_id}" 
    stored_msg=redis_client.lrange(key,-limit,-1)
    messages=[]
    for msg in stored_msg:
        m=json.loads(msg)
        if m['role']=='user':
            messages.append(HumanMessage(m['content']))
        else:
            messages.append(AIMessage(m['content']))
    print('stored message in redis :' ,messages)
    print("ALL REDIS KEYS:", redis_client.keys("chat:*"))

    return messages

# send this prompt to llm 
model=ChatGoogleGenerativeAI(model="gemini-2.5-flash")
model2=ChatOpenAI(model="nvidia/nemotron-3-nano-30b-a3b:free",base_url="https://openrouter.ai/api/v1")

parser=StrOutputParser()
primary_chain=template | model | parser
fallback_chain=template | model2 | parser





