from tavily import TavilyClient
from src.chat import save_chat_in_redis, load_chat_from_redis
import logging
from src.llm.groq_llm import groq_llm
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.messages import AIMessage
logger=logging.getLogger(__name__)
tavily_client = TavilyClient()
web_search_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful AI assistant with access to real-time web search.
 
Your role: Answer the user's query using CURRENT information from web search results.

SEARCH RESULTS:
{search_results}

Guidelines:
- Use the search results to provide accurate, up-to-date information
- Cite sources when mentioning specific facts or data
- If search results are insufficient, say so honestly
- Prioritize recent and authoritative sources
- Keep responses clear and conversational


Now answer the user's query based on the search results above."""),
    ("user", "{query}")
])
parser=StrOutputParser()
web_searcg_chain=web_search_prompt | groq_llm | parser
async def route_web_search(query,guest_id):
    try:
        save_chat_in_redis(guest_id, 'user', query)
        result = tavily_client.search(
            query,
            max_results=2,
            topic="general"
        ) 
        
        
        content=result['results'][-1]['content']
        final_result=web_searcg_chain.invoke({'query':query,'search_results':content})
        save_chat_in_redis(guest_id, 'assistant', AIMessage(final_result).content)
        
        return final_result
        
    except Exception as e:
        logger.error(f"Error searching with Tavily: {str(e)}")
        error_message = f"Search failed: {str(e)}"
        raise
