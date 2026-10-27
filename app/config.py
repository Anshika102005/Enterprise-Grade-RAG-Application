import app._hf_env  # noqa: F401 — must precede huggingface_hub/sentence-transformers
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)


class Settings:

    # --- HUGGING FACE EMBEDDINGS ---
    HUGGINGFACE_EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"


    # --- VECTOR DB (QDRANT) ---
    QDRANT_URL = os.getenv("QDRANT_CLUSTER_ENDPOINT")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION = "rag-v1"

    # --- LOGFIRE (OBSERVABILITY) ---
    LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN")

    # --- REASONING ENGINE (GROQ) ---
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = "openai/gpt-oss-20b"
    GROQ_FALLBACK_API_KEY = os.getenv("GROQ_FALLBACK_API_KEY")

    # --- LLM GATEWAY (PORTKEY) ---
    PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY")
    GROQ_SLUG =  "rag"     # primary: @rag/llama-3.3-70b-versatile
    GROQ_SLUG_2 = "brag"  # fallback: @brag/llama-3.1-8b-instant
    
    # --- CORS (React frontend) ---
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
        ).split(",")
        if origin.strip()
    ]

    # --- HYBRID RETRIEVAL ---
    # Dense vectors (semantic) are fused with BM25 sparse vectors via Reciprocal
    # Rank Fusion, then reranked by the FlashRank cross-encoder.
    RETRIEVAL_DENSE_TOP_K = int(os.getenv("RETRIEVAL_DENSE_TOP_K", "20"))
    RETRIEVAL_SPARSE_TOP_K = int(os.getenv("RETRIEVAL_SPARSE_TOP_K", "20"))
    RETRIEVAL_FUSED_TOP_K = int(os.getenv("RETRIEVAL_FUSED_TOP_K", "15"))
    RRF_K = int(os.getenv("RRF_K", "60"))
    RERANK_TOP_N = int(os.getenv("RERANK_TOP_N", "5"))

    # --- SELF-RAG (CORRECTIVE RETRIEVAL LOOP) ---
    MAX_RETRIEVAL_RETRIES = int(os.getenv("MAX_RETRIEVAL_RETRIES", "2"))

    # --- EVALUATION JUDGE (RAGAS / DeepEval) ---
    # Separate quota key so eval calls never eat into production traffic.
    JUDGE_API_KEY = os.getenv("JUDGE_GROQ") or os.getenv("GROQ_API_KEY")
    JUDGE_MODEL = os.getenv("JUDGE_MODEL", "openai/gpt-oss-20b")

    # --- OBSERVABILITY ---
    LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "true")
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "rag_scale_test")
    LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

# Apply LangChain environment variables for automatic tracing
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGSMITH_TRACING", "true")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "rag_scale_test")
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

settings = Settings()