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
     "You are a document assistant. Answer based ONLY on the context provided.\n\n"
     "MOST IMPORTANT RULE - LANGUAGE MATCHING:\n"
     "You MUST respond in the EXACT SAME language as the user's question.\n\n"
     "Examples:\n"
     "- User asks: 'What is attention mechanism?' → You answer in ENGLISH\n"
     "- User asks: 'attention mechanism kya hai?' → You answer in HINDI\n"
     "- User asks: 'explain attention' → You answer in ENGLISH\n"
     "- User asks: 'attention ke bare me batao' → You answer in HINDI\n\n"
     "ANSWER RULES:\n"
     " If context has the answer:\n"
     "   - Provide detailed explanation in user's language\n"
     "   - Use simple, clear words\n"
     "   - Stay accurate to the context\n\n"
     " If context does NOT have the answer:\n"
     "   - For English: 'I don't have information about that in the documents. The documents cover [mention topics]. Can I help with something else?'\n"
     "   - For Hindi: 'मुझे इसके बारे में दस्तावेज़ में जानकारी नहीं मिली। दस्तावेज़ में [topics] है। क्या मैं कुछ और बता सकता हूं?'\n\n"
     "NEVER:\n"
     "- Mix English and Hindi in same response\n"
     "- Make up information\n"
     "- Change the user's language\n\n"
     "DOCUMENT CONTEXT:\n{context}\n\n"
     "---\n"
     "Now answer in the SAME language as the user's question."
    ),
    MessagesPlaceholder(variable_name='chat_history'),
    ('human', '{query}')
])#local
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
    logger.info(f'stored message in redis : {messages}')
    logger.info(f'ALL REDIS KEYS:" {redis_client.keys("chat:*")}')

    return messages

# send this prompt to llm 
model=ChatGoogleGenerativeAI(model="gemini-2.5-flash")
model2=ChatOpenAI(model="nvidia/nemotron-3-nano-30b-a3b:free",base_url="https://openrouter.ai/api/v1")

parser=StrOutputParser()
primary_chain=template | model | parser
fallback_chain=template | model2 | parser





