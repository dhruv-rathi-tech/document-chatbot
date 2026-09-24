import os
from pathlib import Path
from dotenv import load_dotenv

# Project Paths
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

import tempfile

# Base directory where all per-session data lives (uploads + vector DBs).
# In Hugging Face Spaces (SPACE_ID present), use system temp directory to ensure write permissions.
if os.getenv("SPACE_ID") or os.getenv("SESSIONS_DIR"):
    SESSIONS_DIR = Path(os.getenv("SESSIONS_DIR", str(Path(tempfile.gettempdir()) / "docmate_sessions")))
else:
    SESSIONS_DIR = BASE_DIR / "data" / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def get_session_paths(session_id: str):
    session_dir = SESSIONS_DIR / session_id
    dataset_dir = session_dir / "dataset"
    chroma_dir = session_dir / "chroma_db"

    dataset_dir.mkdir(parents=True, exist_ok=True)
    chroma_dir.mkdir(parents=True, exist_ok=True)

    return dataset_dir, chroma_dir


# ChromaDB
COLLECTION_NAME = "user_docs"

# Chunking
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Embedding Model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Retrieval
DENSE_TOP_K = 15
BM25_TOP_K = 15

# Reranker
RERANK_TOP_K = 6
RERANK_MODEL = "BAAI/bge-reranker-base"

# Generation
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

LLM_MODEL = "gemini-2.5-flash"
TEMPERATURE = 0.1

# Evaluation
DENSE_DISTANCE_THRESHOLD = 1.05
BM25_SCORE_THRESHOLD = 8
RERANKED_SCORE_THRESHOLD = 0.05

# Upload constraints
MAX_FILE_SIZE_MB = 20
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".txt", ".md"}
