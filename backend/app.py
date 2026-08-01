import os
import shutil
import uuid
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.config import (

    get_session_paths,
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_MB,
    SESSIONS_DIR,
)
from src.ingestion.ingest import load_documents, split_documents
from src.embeddings.embedding import create_vector_db, get_embedding_model
from src.retrieval.retrieve import HybridRetriever
from src.reranking.rerank import rerank, get_reranker
from src.generation.generate import generate
from src.evaluation.evaluate import evaluate_retrieval, evaluate_reranker


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up embedding and reranker models on app startup
    try:
        get_embedding_model()
    except Exception as e:
        print(f"Embedding model warmup warning: {e}")
    try:
        get_reranker()
    except Exception as e:
        print(f"Reranker model warmup warning: {e}")
    yield


app = FastAPI(title="RAG Chatbot API", lifespan=lifespan)

raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False if "*" in origins else True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# In-memory registry of which sessions have a ready vector DB + retriever loaded, so /chat doesn't reload BM25/Chroma from disk on every message.
active_retrievers: dict[str, HybridRetriever] = {}
session_sources: dict[str, list[str]] = {}

class ChatRequest(BaseModel):
    session_id: str
    query: str

class ChatResponse(BaseModel):
    answer: str

class UploadResponse(BaseModel):
    session_id: str
    files_processed: list[str]
    chunks_indexed: int


@app.get("/")
def health_check():
    return {"status": "ok", "message": "RAG Chatbot API is running."}


@app.post("/upload", response_model=UploadResponse)
async def upload_documents(
    files: list[UploadFile] = File(...),
    session_id: str | None = Form(default=None),
):

    if not session_id:
        session_id = str(uuid.uuid4())

    dataset_dir, chroma_dir = get_session_paths(session_id)

    saved_names = []
    for upload in files:
        suffix = Path(upload.filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{suffix}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
            )

        contents = await upload.read()
        size_mb = len(contents) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"File '{upload.filename}' exceeds the {MAX_FILE_SIZE_MB}MB limit.",
            )

        dest_path = dataset_dir / upload.filename
        with open(dest_path, "wb") as f:
            f.write(contents)
        saved_names.append(upload.filename)

    if not saved_names:
        raise HTTPException(status_code=400, detail="No valid files were uploaded.")

    try:
        documents = load_documents(dataset_dir=dataset_dir)
        if not documents:
            raise HTTPException(
                status_code=400,
                detail="Could not extract any text from the uploaded file(s).",
            )

        chunks = split_documents(documents)
        create_vector_db(chunks, chroma_dir=chroma_dir)

        retriever = HybridRetriever()
        retriever.load_vector_db(chroma_dir=chroma_dir)
        active_retrievers[session_id] = retriever
        session_sources[session_id] = saved_names

        return UploadResponse(
            session_id=session_id,
            files_processed=saved_names,
            chunks_indexed=len(chunks),
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process documents: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        retriever = active_retrievers.get(request.session_id)

        if retriever is None:
            _, chroma_dir = get_session_paths(request.session_id)
            if not chroma_dir.exists() or not any(chroma_dir.iterdir()):
                raise HTTPException(
                    status_code=404,
                    detail="No documents found for this session. Please upload documents first.",
                )
            retriever = HybridRetriever()
            retriever.load_vector_db(chroma_dir=chroma_dir)
            active_retrievers[request.session_id] = retriever

        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty.")

        retrieval_results = retriever.hybrid_retrieve(request.query)
        retrieval_results = evaluate_retrieval(retrieval_results)

        if not retrieval_results:
            return ChatResponse(
                answer="I don't have enough information in the provided documents to answer this question."
            )

        reranked_results = rerank(request.query, retrieval_results)
        reranked_results = evaluate_reranker(reranked_results)

        if not reranked_results:
            return ChatResponse(
                answer="I don't have enough information in the provided documents to answer this question."
            )

        answer = generate(request.query, reranked_results)
        return ChatResponse(answer=answer)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error during chat: {str(e)}")



@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    """Deletes a session's uploaded files and vector DB (temporary storage cleanup)."""
    active_retrievers.pop(session_id, None)
    session_sources.pop(session_id, None)

    session_dir = SESSIONS_DIR / session_id
    if session_dir.exists():
        shutil.rmtree(session_dir)

    return {"status": "deleted", "session_id": session_id}
