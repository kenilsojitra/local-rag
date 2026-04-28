import os
import shutil
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from retrieval.retrieve import get_retriever
from ingestion.ingest import process_and_store_documents, CHROMA_DIR, BM25_FILE, DATA_DIR

app = FastAPI()

# Mount the static directory
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

class ChatRequest(BaseModel):
    query: str
    history: Optional[List[dict]] = []

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def format_history(history):
    formatted = ""
    for msg in history:
        role = "User" if msg.get("role") == "user" else "Assistant"
        formatted += f"{role}: {msg.get('content')}\n"
    return formatted

@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        llm = Ollama(model="mistral")
    except Exception as e:
        return {"error": f"Error initializing Ollama: {e}"}

    try:
        retriever = get_retriever()
    except Exception as e:
        return {"error": f"Error loading retriever: {e}. Have you ingested any documents yet?"}

    prompt = PromptTemplate.from_template(
        "You are an expert assistant. Use the following retrieved context to answer the user's question accurately. "
        "If the answer cannot be found in the context, explicitly state that you don't know. Do not make up information.\n\n"
        "### Chat History:\n{chat_history}\n\n"
        "### Context:\n{context}\n\n"
        "### Question:\n{question}\n\n"
        "### Answer:\n"
    )

    qa_chain = (
        {
            "context": retriever | format_docs, 
            "question": RunnablePassthrough(),
            "chat_history": lambda x: format_history(req.history)
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    async def generate():
        try:
            for chunk in qa_chain.stream(req.query):
                yield chunk
        except Exception as e:
            yield f"\n\nError: {str(e)}"

    return StreamingResponse(generate(), media_type="text/plain")

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    # Create data dir if not exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    saved_files = []
    for file in files:
        file_path = os.path.join(DATA_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file.filename)
        
    # Clear old vector DBs to prevent duplicate ingestion since we re-ingest all
    if os.path.exists(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR)
    if os.path.exists(BM25_FILE):
        os.remove(BM25_FILE)
        
    # Re-ingest
    try:
        process_and_store_documents()
        return {"status": "success", "message": f"Successfully uploaded and ingested {len(saved_files)} files.", "files": saved_files}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
