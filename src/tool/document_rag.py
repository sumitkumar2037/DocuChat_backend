from src.modelCall import query_retrival
from src.chat import primary_chain,load_chat_from_redis,fallback_chain,save_chat_in_redis
from dotenv import load_dotenv
from langchain.messages import AIMessage
load_dotenv()
import logging
logger=logging.getLogger(__name__)
async def route_dacument_rag(query,guest_id):
    save_chat_in_redis(guest_id,'user',query)
    chat_history=load_chat_from_redis(guest_id,10)
    # logger.info(f'current chat history : {chat_history}')
    context=await query_retrival(query,guest_id)
    result=""
    try:
        result =  primary_chain.invoke({
        "chat_history": chat_history,
        "context": context,
        "query": query
    })
    except Exception as primary_error:
        print("Primary LLM failed:", primary_error)
        try:
            result =  fallback_chain.invoke({
                "chat_history": chat_history,
                "context": context,
                "query": query
            })
        except Exception as fallback_error:
             logger.info(f"Fallback LLM failed: {fallback_error}")

        return {
            "ai_message": "AI services are currently unavailable."
        }
    
    return result
