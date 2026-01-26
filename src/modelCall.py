from src.model import pc , embed_chunk_to_pinecone,load_files_from_folder


# dynamic query 
async def query_retrival(query:str,guest_id)->str:
    retriever = pc.as_retriever(
    search_type="similarity",   
    search_kwargs={"k": 4,'guest_id':guest_id}
    )
    docs=retriever.invoke(query)
    context = ""
    for d in docs:
        context += d.page_content + "\n\n"
    return context

if __name__=="__main__":
    query_retrival("",'')
    




