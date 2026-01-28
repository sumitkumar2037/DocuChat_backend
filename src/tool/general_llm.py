from src.classifer.classifier_tool import take_user_query
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import tool
from langchain_core.output_parsers import StrOutputParser
from src.chat import save_chat_in_redis,load_chat_from_redis
from langchain.messages import AIMessage
load_dotenv()
   
prompt=ChatPromptTemplate.from_messages([
    ("system", """You are a helpful AI assistant.

Your role: Answer questions using general knowledge in a natural, conversational way.

Guidelines:
- Be clear, accurate, and friendly
- Use conversation history for context
- Admit when you're uncertain
- Provide examples when helpful
- Keep responses conversational, not overly formal

Engage naturally with the user's question."""),
    ("placeholder", "{chat_history}"),
    ("user", "{query}")
])
llm1=ChatGroq(model='openai/gpt-oss-safeguard-20b')
llm2=ChatOpenAI(base_url='https://openrouter.ai/api/v1',model='nvidia/nemotron-3-nano-30b-a3b:free')
parser=StrOutputParser()


async def route_general_llm(query:str,guest_id:str)->str:
    save_chat_in_redis(guest_id,'user',query)
    general_llm_chain=prompt | llm1 | parser
    chat_history=load_chat_from_redis(guest_id)
    result=general_llm_chain.invoke({'query':query,'chat_history':chat_history})
    return result

 




