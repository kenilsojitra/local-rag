# Local RAG System (100% Offline)

A fully offline, privacy-preserving Retrieval-Augmented Generation (RAG) system designed to run on standard consumer hardware (optimized for 16GB RAM, no GPU required).

This project allows you to build a local knowledge base from your own documents (TXT, CSV, etc.) and chat with it using advanced open-source AI models, all without your data ever leaving your machine!

## Features

- **100% Offline & Private:** No internet connection required once the models are downloaded. Your data stays on your machine.
- **CPU Friendly:** Optimized to run smoothly on standard computers with 16GB RAM without needing a dedicated graphics card (GPU).
- **Advanced RAG Capabilities:** Implements Semantic Chunking, Hybrid Search (Dense + BM25 Sparse), and Contextual Reranking (Cross-Encoder) for production-grade retrieval accuracy.
- **Multiple File Formats:** Out-of-the-box support for reading `.txt` and `.csv` files.
- **Real-Time Streaming:** Watch the AI generate answers word-by-word just like ChatGPT.
- **Modern Tech Stack:** Built with the latest LCEL (LangChain Expression Language) architecture.

## Tech Stack

- **Framework:** [LangChain](https://python.langchain.com/) & LangChain Experimental
- **Vector Database:** [ChromaDB](https://www.trychroma.com/) (Dense Search)
- **Sparse Index:** BM25 (Keyword Search)
- **Embeddings:** `all-MiniLM-L6-v2` (via Hugging Face)
- **Reranker:** `cross-encoder/ms-marco-MiniLM-L-6-v2` (via Hugging Face)
- **Local LLM:** `mistral:7b` (via Ollama)

---

## Getting Started

Follow these steps to set up the project locally on your machine.

### 1. Prerequisites

1. **Python 3.9+** installed on your system.
2. **[Ollama](https://ollama.com/)** installed on your system (used to run the AI model locally).

### 2. Clone the Repository

```bash
git clone https://github.com/your-username/local-rag.git
cd local-rag
```

### 3. Setup Virtual Environment & Install Dependencies

It is highly recommended to use a virtual environment. We use `uv` for dependency management because it is incredibly fast (written in Rust) and significantly speeds up installation times compared to standard pip.

```bash
# Install uv (if you haven't already)
pip install uv

# Create a virtual environment instantly
uv venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

# Install the required Python packages blazingly fast!
uv pip install -r requirements.txt
```

### 4. Download the Local LLM

We use Mistral 7B as it offers the best balance of speed and intelligence for a 16GB RAM setup. Make sure Ollama is running, then execute:

```bash
ollama pull mistral
```
*(Note: If you have less RAM or want faster CPU inference, you can also try `ollama pull phi3` or `ollama pull llama3`)*

---

## Usage

### Step 1: Add Your Data
Create a folder named `data/` in the root directory (if it doesn't exist) and drop your files inside it. 
Currently, the script is configured to automatically process `.txt` and `.csv` files.

### Step 2: Ingest the Documents
Run the ingestion script. This will read your files, split them semantically using an embedding-aware chunker, and build both a dense vector index (`chroma_db/`) and a sparse keyword index (`bm25_retriever.pkl`).

```bash
python -m ingestion.ingest
```
*(Note: The first time you run this, it will download a small embedding model (~90MB) from Hugging Face. The vectorization process may take a few minutes depending on your CPU and the size of your dataset).*

### Step 3: Chat with your Data!
Once ingestion is complete, start the command-line interface to interact with your local RAG system:

```bash
python app.py
```

Ask a question, and the AI will retrieve the most relevant context from your documents and stream the answer back to you! Type `exit` or `quit` to close the application.

---

## Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

