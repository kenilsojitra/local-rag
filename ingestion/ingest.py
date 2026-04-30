import os
import pickle
from langchain_community.document_loaders import DirectoryLoader, TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

# Directories
DATA_DIR = "data"
CHROMA_DIR = "chroma_db"
BM25_FILE = "bm25_retriever.pkl"

def load_documents(data_dir=DATA_DIR):
    """Loads all documents from the data directory."""
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created directory {data_dir}. Please put some documents there and run again.")
        return []

    txt_loader = DirectoryLoader(data_dir, glob="**/*.txt", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"})
    csv_loader = DirectoryLoader(data_dir, glob="**/*.csv", loader_cls=CSVLoader, loader_kwargs={"encoding": "utf-8"})
    
    docs = txt_loader.load()
    try:
        docs.extend(csv_loader.load())
    except Exception as e:
        print(f"Warning loading CSVs: {e}")
        
    return docs

def process_and_store_documents():
    print("Loading documents...")
    docs = load_documents()
    
    if not docs:
        print("No documents found to ingest.")
        return

    print(f"Loaded {len(docs)} documents. Splitting into chunks...")
    
    # 2. Chunking (Performant Semantic Boundaries)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(docs)
    
    print(f"Created {len(chunks)} chunks. Initializing Embeddings...")

    # 3. Embeddings
    # Lightweight embeddings suitable for 16GB RAM as per docs.txt
    emb = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )
    
    print("Storing in ChromaDB and BM25...")

    # 4. Store in ChromaDB (Dense Vector Search)
    Chroma.from_documents(
        documents=chunks,
        embedding=emb,
        persist_directory=CHROMA_DIR
    )
    
    # 5. Create and save BM25 Retriever (Sparse Keyword Search)
    bm25_retriever = BM25Retriever.from_documents(chunks)
    
    with open(BM25_FILE, "wb") as f:
        pickle.dump(bm25_retriever, f)
    
    print(f"Successfully ingested {len(chunks)} chunks into {CHROMA_DIR} and {BM25_FILE}!")

def rebuild_bm25():
    """Rebuilds the BM25 index from documents currently in ChromaDB."""
    emb = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma(persist_directory=CHROMA_DIR, embedding_function=emb)
    
    db_data = db.get()
    docs = []
    if db_data and "documents" in db_data and db_data["documents"]:
        for text, meta in zip(db_data["documents"], db_data["metadatas"]):
            docs.append(Document(page_content=text, metadata=meta))
    
    if not docs:
        if os.path.exists(BM25_FILE):
            os.remove(BM25_FILE)
        print("No documents in ChromaDB, removed BM25 file.")
        return
        
    bm25_retriever = BM25Retriever.from_documents(docs)
    with open(BM25_FILE, "wb") as f:
        pickle.dump(bm25_retriever, f)
    print(f"Rebuilt BM25 index with {len(docs)} chunks.")

if __name__ == "__main__":
    process_and_store_documents()
