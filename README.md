# Nexus RAG — Local AI Agent

A fully offline, privacy-preserving Retrieval-Augmented Generation (RAG) system with an Agentic architecture. Runs on standard consumer hardware (optimized for 16GB RAM, no GPU required). Your data never leaves your machine.

## Features

- **100% Local & Private** — No cloud APIs. Ollama runs the LLM on your CPU.
- **Agentic RAG** — The AI decides whether to search your documents, search the web (DuckDuckGo), or use a calculator — automatically.
- **Hybrid Search** — Combines dense vector search (ChromaDB) + sparse keyword search (BM25) for best-of-both retrieval.
- **Contextual Reranking** — Cross-encoder reranks retrieved chunks before sending to the LLM.
- **Source Citations** — Every answer shows which document and passage it came from.
- **Chat History (MongoDB)** — All conversations are persisted to a local MongoDB database. Full history dashboard with charts.
- **Document Management** — Upload, view chunk counts, and delete documents from the UI.
- **Model Caching** — Embedding model, reranker, and LLM are loaded once at startup for fast responses.
- **Modern Web UI** — Streaming responses, drag-and-drop uploads, sources sidebar.

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | `mistral:7b` via [Ollama](https://ollama.com/) |
| Agent Framework | LangChain ReAct Agent |
| Vector DB | [ChromaDB](https://www.trychroma.com/) |
| Sparse Index | BM25 (`rank_bm25`) |
| Embeddings | `all-MiniLM-L6-v2` (HuggingFace) |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` (HuggingFace) |
| Web Search | DuckDuckGo (`ddgs`) |
| Backend | FastAPI + Uvicorn |
| History DB | MongoDB (local) |
| Frontend | Vanilla JS + Chart.js |

---

## Getting Started

### Prerequisites

1. **Python 3.9+**
2. **[Ollama](https://ollama.com/)** installed and running
3. **[MongoDB Community Server](https://www.mongodb.com/try/download/community)** installed and running locally on port `27017`
4. **[uv](https://github.com/astral-sh/uv)** (fast Python package manager)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/local-rag.git
cd local-rag
```

### 2. Create Virtual Environment & Install Dependencies

```bash
# Install uv if you haven't already
pip install uv

# Create venv and install all dependencies
uv venv
uv pip install -r requirements.txt
```

### 3. Pull the LLM

```bash
ollama pull mistral
```

> For lower RAM machines try `ollama pull phi3` or `ollama pull llama3`

### 4. Start MongoDB

Make sure MongoDB is running locally:

```bash
# Windows (if not running as a service)
"C:\Program Files\MongoDB\Server\<version>\bin\mongod.exe" --dbpath C:\data\db

# Mac/Linux
mongod --dbpath /data/db
```

### 5. Run the Server

```bash
.venv\Scripts\uvicorn.exe server:app --host 0.0.0.0 --port 8000 --reload
# Mac/Linux:
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

Open **http://localhost:8000** in your browser.

---

## Usage

### Uploading Documents
- Drag and drop `.txt` or `.csv` files onto the upload zone in the sidebar.
- The system automatically chunks, embeds, and indexes them.
- Use **Manage Documents** to view chunk counts or delete files.

### Chatting
- Ask anything — the agent will automatically decide whether to:
  - Search your local documents (RAG)
  - Search the web (DuckDuckGo)
  - Perform a calculation (Calculator)
- Source citations appear in a side panel after each answer.

### Chat History
- Click **Chat History** in the sidebar to open the history dashboard.
- View all past sessions, read full conversations, and delete sessions.
- Charts show messages per day and user vs AI ratio.

---

## Project Structure

```
local-rag/
├── server.py           # FastAPI app — all API routes
├── ingestion/
│   └── ingest.py       # Document loading, chunking, ChromaDB + BM25 indexing
├── retrieval/
│   └── retrieve.py     # Hybrid retriever with reranking (models cached at startup)
├── db/
│   └── mongo.py        # MongoDB helpers for chat history
├── static/
│   ├── index.html      # Main chat UI
│   ├── history.html    # History dashboard with charts
│   ├── script.js       # Frontend logic
│   └── style.css       # Styles
└── data/               # Drop your documents here
```

---

## Contributing

Contributions, issues, and feature requests are welcome!
