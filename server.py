import os
import shutil
import uuid
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

import json
from langchain_ollama import OllamaLLM as Ollama
from langchain_core.prompts import PromptTemplate
from retrieval.retrieve import get_retriever
from ingestion.ingest import process_and_store_documents, rebuild_bm25, CHROMA_DIR, BM25_FILE, DATA_DIR
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_classic.tools.retriever import create_retriever_tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_classic.chains import LLMMathChain
from langchain_core.tools import Tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from db.mongo import save_message, get_sessions, get_session_messages, delete_session, get_stats

app = FastAPI()

# Cached at startup — never reloaded per request
_llm = None

def get_llm():
    global _llm
    if _llm is None:
        print("Loading Ollama LLM (one-time)...")
        _llm = Ollama(model="mistral")
    return _llm

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/history")
async def history_page():
    return FileResponse("static/history.html")

class ChatRequest(BaseModel):
    query: str
    history: Optional[List[dict]] = []
    session_id: Optional[str] = None

def format_history(history):
    formatted = ""
    for msg in history:
        role = "User" if msg.get("role") == "user" else "Assistant"
        formatted += f"{role}: {msg.get('content')}\n"
    return formatted

@app.post("/api/chat")
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())

    llm = get_llm()

    try:
        retriever = get_retriever()
    except Exception as e:
        return {"error": f"Error loading retriever: {e}. Have you ingested any documents yet?"}

    rag_tool = create_retriever_tool(
        retriever,
        "LocalRAG",
        "Searches and returns excerpts from the user's local documents. Use this tool whenever you need to answer questions about the user's uploaded files. Make sure to cite the source file in your final answer."
    )
    search_tool = DuckDuckGoSearchRun(name="WebSearch", description="Searches the internet using DuckDuckGo. Use this tool to answer questions about current events or general knowledge outside the local documents.")

    try:
        math_chain = LLMMathChain.from_llm(llm=llm)
        math_tool = Tool(
            name="Calculator",
            func=math_chain.run,
            description="Useful for when you need to answer questions about math or calculations."
        )
        tools = [rag_tool, search_tool, math_tool]
    except Exception as e:
        print(f"Warning: Could not initialize Calculator tool: {e}")
        tools = [rag_tool, search_tool]

    react_prompt = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Previous conversation history:
{chat_history}

Question: {input}
Thought:{agent_scratchpad}"""

    prompt = PromptTemplate.from_template(react_prompt)
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

    # Save user message to MongoDB
    try:
        save_message(session_id, "user", req.query)
    except Exception as e:
        print(f"MongoDB save error: {e}")

    async def generate():
        full_response = ""
        try:
            yield f"[[SESSION_ID]]{session_id}\n"

            async for event in agent_executor.astream_events(
                {"input": req.query, "chat_history": format_history(req.history)},
                version="v1"
            ):
                kind = event["event"]
                name = event.get("name", "")

                # Show which tool is being used as a status indicator
                if kind == "on_tool_start":
                    yield f"\n\n*Using tool: {name}...*\n\n"

                # Emit source citations from the RAG retriever
                elif kind == "on_retriever_end":
                    docs = event["data"].get("output", [])
                    if docs:
                        for d in docs:
                            source_data = {
                                "source": d.metadata.get("source", "Unknown"),
                                "content": d.page_content
                            }
                            yield f"\n[[SOURCE]]{json.dumps(source_data)}\n"

                # The AgentExecutor chain_end carries the final "output" key
                elif kind == "on_chain_end" and name == "AgentExecutor":
                    output = event["data"].get("output", {})
                    answer = output.get("output", "") if isinstance(output, dict) else str(output)
                    if answer:
                        full_response = answer
                        yield answer

        except Exception as e:
            yield f"\n\nError: {str(e)}"
        finally:
            # Save assistant response to MongoDB
            if full_response:
                try:
                    save_message(session_id, "assistant", full_response)
                except Exception as e:
                    print(f"MongoDB save error: {e}")

    return StreamingResponse(generate(), media_type="text/plain")

# --- History API ---

@app.get("/api/history/sessions")
async def list_sessions():
    try:
        sessions = get_sessions()
        for s in sessions:
            s["updated_at"] = s["updated_at"].isoformat() if hasattr(s["updated_at"], "isoformat") else str(s["updated_at"])
            s["created_at"] = s["created_at"].isoformat() if hasattr(s["created_at"], "isoformat") else str(s["created_at"])
        return {"sessions": sessions}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/history/sessions/{session_id}")
async def get_session(session_id: str):
    try:
        msgs = get_session_messages(session_id)
        return {"messages": msgs}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.delete("/api/history/sessions/{session_id}")
async def remove_session(session_id: str):
    try:
        delete_session(session_id)
        return {"status": "success"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/history/stats")
async def history_stats():
    try:
        return get_stats()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# --- Documents API ---

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    os.makedirs(DATA_DIR, exist_ok=True)
    saved_files = []
    for file in files:
        file_path = os.path.join(DATA_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file.filename)

    if os.path.exists(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR)
    if os.path.exists(BM25_FILE):
        os.remove(BM25_FILE)

    try:
        process_and_store_documents()
        return {"status": "success", "message": f"Successfully uploaded and ingested {len(saved_files)} files.", "files": saved_files}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/documents")
async def get_documents():
    if not os.path.exists(DATA_DIR):
        return {"documents": []}

    files = os.listdir(DATA_DIR)
    chunk_counts = {}
    if os.path.exists(CHROMA_DIR):
        try:
            emb = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            db = Chroma(persist_directory=CHROMA_DIR, embedding_function=emb)
            db_data = db.get()
            if db_data and "metadatas" in db_data and db_data["metadatas"]:
                for meta in db_data["metadatas"]:
                    src = meta.get("source", "")
                    filename = os.path.basename(src)
                    chunk_counts[filename] = chunk_counts.get(filename, 0) + 1
        except Exception as e:
            print("Error reading Chroma DB:", e)

    return {"documents": [{"filename": f, "chunks": chunk_counts.get(f, 0)} for f in files]}

@app.delete("/api/documents/{filename}")
async def delete_document(filename: str):
    file_path = os.path.join(DATA_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    if os.path.exists(CHROMA_DIR):
        try:
            emb = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            db = Chroma(persist_directory=CHROMA_DIR, embedding_function=emb)
            db_data = db.get()
            ids_to_delete = []
            if db_data and "metadatas" in db_data and db_data["metadatas"]:
                for doc_id, meta in zip(db_data["ids"], db_data["metadatas"]):
                    src = meta.get("source", "")
                    if os.path.basename(src) == filename:
                        ids_to_delete.append(doc_id)
            if ids_to_delete:
                db.delete(ids=ids_to_delete)
                rebuild_bm25()
        except Exception as e:
            return {"status": "error", "message": f"Failed to delete chunks: {str(e)}"}

    return {"status": "success", "message": f"Deleted {filename}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
