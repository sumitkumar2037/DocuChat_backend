from llm.groq_llm import groq_llm
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
load_dotenv()

prompt=ChatPromptTemplate.from_messages(
    ('system',"""Condense the following file text  by shortening and summarizing the content 
without losing important information in 400-600 words:\n{file_text}\nCondensed Transcript:
""")
)
parser=StrOutputParser()
summary_chain=prompt | groq_llm | parser
async def get_summary(file_text:str):
    result=summary_chain.invoke({'full_text':file_text})
    return result




if __name__=='__main__':
    get_summary('')
    
