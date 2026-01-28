from langchain_openai import ChatOpenAI
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader,PyPDFLoader,TextLoader,Docx2txtLoader
from pinecone import Pinecone
import glob
import os
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from fastapi import Depends
import asyncio
#load the all api key
load_dotenv()

#session wise document load 
def get_loader(file_path):
    file_type=os.path.splitext(file_path)[1].lower()
    if file_type=='.pdf':
        return PyPDFLoader(file_path)
    if file_type=='.docx':
        return Docx2txtLoader(file_path)
    if file_type=='.txt':
        return TextLoader(file_path,encoding="utf-8")
    else:
        return None
    

async def load_files_from_folder(guest_id:str):
    if not guest_id:
        return []
    all_docs=[]
    folder_path=f"items/{guest_id}"
    files=[]
    files.extend(glob.glob(f"{folder_path}/*.pdf"))
    files.extend(glob.glob(f"{folder_path}/*.txt"))
    files.extend(glob.glob(f"{folder_path}/*.docx"))

    load=asyncio.get_running_loop()

    for file_path in files:
        
        loader=get_loader(file_path)
        if not loader:
            continue
        docs=await load.run_in_executor(
        None,
        loader.load
    )
        #attach meta deta 
        for d in docs:
            d.metadata['guest_id']=guest_id
            d.metadata['source']=file_path
        all_docs.extend(docs)

    return all_docs

#chunk all the doc=list[Document]
text_splitter=RecursiveCharacterTextSplitter(
    chunk_size=1200,
    chunk_overlap=200
)

#embedding vector model  
google_embedding=GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
)
pc_index="langchain" 
pc=PineconeVectorStore(
    embedding=google_embedding,
    index_name=pc_index
)
def embed_chunk_to_pinecone(session_id:str,docs:list):
    chunk=text_splitter.split_documents(docs)
    pc.add_documents(chunk)



if __name__=='__main__':
    embed_chunk_to_pinecone('',[])
    

    






