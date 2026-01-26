#this is classifier file which take user query and classify into required calling tool
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from pydantic import BaseModel,Field
from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.store.classifier_context import load_metadata,load_summary
load_dotenv()
llm=ChatGroq(model='openai/gpt-oss-120b')
llm1=ChatGoogleGenerativeAI(model='gemini-3-flash-preview')
class Router_tool(BaseModel):
    route:Literal['DOCUMENT_RAG','WEB_SEARCH','GENERAL_LLM']= Field(
        description="The route to take based on the query type"
    )
    
parser=JsonOutputParser(pydantic_object=Router_tool)
structured_llm = llm.with_structured_output(Router_tool)
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an intelligent query router for a RAG-powered chat system.

Your job: Analyze the user's query and route it to the BEST tool to answer it.

AVAILABLE ROUTES:
1. DOCUMENT_RAG - Search uploaded documents
2. WEB_SEARCH - Search the internet for current information  
3. GENERAL_LLM - Use general AI knowledge

USER'S UPLOADED DOCUMENTS:
- metadata: {metadata}
- Summary: {summary}

ROUTING RULES:

Route to DOCUMENT_RAG if:
✓ Query mentions ANY topic from the document keywords
✓ Query asks about data, numbers, or specifics likely in the document
✓ Query uses phrases like "in my document", "what does it say", "summarize"
✓ Query asks follow-up questions about previously discussed document content
✓ The document summary suggests it contains relevant information

Route to WEB_SEARCH if:
✓ Query asks about current events, news, or "today/latest/recent"
✓ Query needs real-time data (weather, stock prices, sports scores)
✓ Query asks about events after the document was created
✓ Query explicitly asks to "search the web" or "look up online"

Route to GENERAL_LLM if:
✓ Query asks for explanations, definitions, or how-to guides
✓ Query is about general knowledge unrelated to document topics
✓ Query asks for creative content, coding help, or brainstorming
✓ No documents uploaded AND not asking for current information

IMPORTANT:
- When in doubt between DOCUMENT_RAG and GENERAL_LLM, choose DOCUMENT_RAG if any keywords match
- Always prefer DOCUMENT_RAG if the user uploaded documents and the query could be answered by them
- Only use GENERAL_LLM when you're confident the document can't help

EXAMPLES:
Query: "What's the revenue in Q3?" + keywords contain "revenue, Q3" → DOCUMENT_RAG
Query: "What's the weather today?" → WEB_SEARCH
Query: "Explain machine learning" + no ML keywords in document → GENERAL_LLM
Query: "Tell me more about that" + previous context about document → DOCUMENT_RAG
Query: "What are the latest AI news?" → WEB_SEARCH
Query: "Summarize the key points" → DOCUMENT_RAG

     most important 
     DO NOT respond conversationally. ONLY classify the query.
     You must return a structured response with the route field.
"""),
    ("user", "Classify this query: {query}")
])
  
def take_user_query(query:str,guest_id:str)->str:
    metadata=load_metadata(guest_id)
    summary=load_summary(guest_id)
    route_chain=prompt | structured_llm
    result=route_chain.invoke({'query':query,'metadata':metadata,'summary':summary})
    print('result:',result)
    return result.route

    

