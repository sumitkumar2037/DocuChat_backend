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
import logging

logger=logging.getLogger(__name__)
#----------------------------------------------
#.       Redis Implemetation
#----------------------------------------------

#load the api key 
load_dotenv()
    
# prompt 
template = ChatPromptTemplate.from_messages([
    ("system", 
     "You are a helpful document assistant. You can communicate in English, Hindi, and Hinglish.\n\n"
     "CRITICAL INSTRUCTIONS:\n"
     "1. ALWAYS respond in the SAME LANGUAGE as the user's question\n"
     "   - If question is in Hindi → Answer in Hindi\n"
     "   - If question is in English → Answer in English\n"
     "   - If question is in Hinglish → Answer in Hinglish\n\n"
     "2. Use ONLY the information from the context below to answer\n"
     "3. Explain technical terms in simple language that matches the user's language\n"
     "4. If the answer exists in context, provide a clear explanation\n"
     "5. If the answer is NOT in context, say:\n"
     "   - In Hindi: 'मुझे इस बारे में दस्तावेज़ में जानकारी नहीं मिली। दस्तावेज़ में [topic] के बारे में जानकारी है। क्या मैं उसमें कुछ और मदद कर सकता हूं?'\n"
     "   - In English: 'I couldn't find information about that in the documents. The documents cover [topic]. Can I help with something else?'\n\n"
     " DOCUMENT CONTEXT:\n"
     "{context}\n\n"
     "Now answer the user's question in their language using only the above context."
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
    logger.info('saved chat in redis instance')
    

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
    logger.info('stored message in redis :' ,messages)
    logger.info("ALL REDIS KEYS:", redis_client.keys("chat:*"))

    return messages

# send this prompt to llm 
model=ChatGoogleGenerativeAI(model="gemini-2.5-flash")
model2=ChatOpenAI(model="nvidia/nemotron-3-nano-30b-a3b:free",base_url="https://openrouter.ai/api/v1")

parser=StrOutputParser()
primary_chain=template | model | parser
fallback_chain=template | model2 | parser





