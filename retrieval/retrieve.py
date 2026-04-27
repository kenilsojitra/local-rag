import os
import pickle
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_classic.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

CHROMA_DIR = "chroma_db"
BM25_FILE = "bm25_retriever.pkl"

def get_retriever():
    """Initializes and returns the Hybrid Retriever with Reranking."""
    # 1. Dense Retriever (Chroma)
    emb = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )
    db = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=emb
    )
    # Fetch more documents initially for better reranking pool
    chroma_retriever = db.as_retriever(search_kwargs={"k": 15})

    # 2. Sparse Retriever (BM25)
    if not os.path.exists(BM25_FILE):
        raise FileNotFoundError(f"{BM25_FILE} not found. Did you run ingestion with the updated skill?")
    
    with open(BM25_FILE, "rb") as f:
        bm25_retriever = pickle.load(f)
    
    # Also fetch 15 documents from BM25
    bm25_retriever.k = 15

    # 3. Hybrid Search (Ensemble)
    ensemble_retriever = EnsembleRetriever(
        retrievers=[chroma_retriever, bm25_retriever],
        weights=[0.5, 0.5]
    )

    # 4. Contextual Reranking
    model = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
    # Select the top 4 most relevant chunks
    compressor = CrossEncoderReranker(model=model, top_n=4)
    
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=ensemble_retriever
    )

    return compression_retriever
