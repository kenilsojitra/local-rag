import os
import pickle
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_classic.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

CHROMA_DIR = "chroma_db"
BM25_FILE = "bm25_retriever.pkl"

# Loaded once at startup, reused for every request
_embeddings = None
_cross_encoder = None


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        print("Loading embedding model (one-time)...")
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings


def _get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        print("Loading reranker model (one-time)...")
        _cross_encoder = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _cross_encoder


def get_retriever():
    """Returns the Hybrid Retriever with Reranking. Models are cached after first call."""
    emb = _get_embeddings()

    db = Chroma(persist_directory=CHROMA_DIR, embedding_function=emb)
    chroma_retriever = db.as_retriever(search_kwargs={"k": 15})

    if not os.path.exists(BM25_FILE):
        raise FileNotFoundError(f"{BM25_FILE} not found. Have you ingested any documents yet?")

    with open(BM25_FILE, "rb") as f:
        bm25_retriever = pickle.load(f)
    bm25_retriever.k = 15

    ensemble_retriever = EnsembleRetriever(
        retrievers=[chroma_retriever, bm25_retriever],
        weights=[0.5, 0.5]
    )

    compressor = CrossEncoderReranker(model=_get_cross_encoder(), top_n=4)

    return ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=ensemble_retriever
    )
