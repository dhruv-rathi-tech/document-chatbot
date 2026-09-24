import os
import sys
import uuid
import shutil
from pathlib import Path

# Disable Gradio SSR mode to prevent port 7861 bind conflict on Hugging Face Spaces
os.environ["GRADIO_SSR_MODE"] = "false"

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import gradio as gr
import uvicorn
from backend.app import app, active_retrievers
from config.config import get_session_paths
from src.ingestion.ingest import load_documents, split_documents
from src.embeddings.embedding import create_vector_db
from src.retrieval.retrieve import HybridRetriever
from src.reranking.rerank import rerank
from src.evaluation.evaluate import evaluate_retrieval, evaluate_reranker
from src.generation.generate import generate


def gradio_upload(files, session_state):
    if not files:
        return "No files uploaded.", session_state
    if not session_state:
        session_state = str(uuid.uuid4())

    dataset_dir, chroma_dir = get_session_paths(session_state)
    saved = []
    for f in files:
        file_path = Path(f.name if hasattr(f, "name") else f)
        dest = dataset_dir / file_path.name
        shutil.copy(str(file_path), str(dest))
        saved.append(file_path.name)

    try:
        docs = load_documents(dataset_dir=dataset_dir)
        if not docs:
            return "Could not extract text from the uploaded file(s).", session_state

        chunks = split_documents(docs)
        create_vector_db(chunks, chroma_dir=chroma_dir)

        retriever = HybridRetriever()
        retriever.load_vector_db(chroma_dir=chroma_dir)
        active_retrievers[session_state] = retriever

        return f"Successfully processed {len(saved)} file(s) ({len(chunks)} chunks indexed). Ready to chat!", session_state
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Processing error: {str(e)}", session_state


def gradio_chat(message, history, session_state):
    if not session_state or session_state not in active_retrievers:
        return "Please upload at least one document first before asking questions."
    try:
        retriever = active_retrievers[session_state]
        retrieval_results = retriever.hybrid_retrieve(message)
        retrieval_results = evaluate_retrieval(retrieval_results)

        if not retrieval_results:
            return "I don't have enough information in the provided documents to answer this question."

        reranked_results = rerank(message, retrieval_results)
        reranked_results = evaluate_reranker(reranked_results)

        if not reranked_results:
            return "I don't have enough information in the provided documents to answer this question."

        return generate(message, reranked_results)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error during generation: {str(e)}"


# Build companion Gradio interface
with gr.Blocks(title="DocMate") as demo:
    session_state = gr.State("")
    gr.Markdown("# 📄 DocMate — AI Document Assistant")
    gr.Markdown("👉 Looking for the custom React UI? **[Open DocMate Web App](/)**")

    with gr.Row():
        file_input = gr.File(
            label="Upload Documents (PDF, Word, PPTX, Excel, TXT, MD)",
            file_count="multiple",
        )
    upload_status = gr.Markdown("")
    file_input.upload(
        gradio_upload,
        inputs=[file_input, session_state],
        outputs=[upload_status, session_state],
    )

    gr.ChatInterface(
        fn=gradio_chat,
        additional_inputs=[session_state],
        type="messages",
    )

# Mount Gradio app onto FastAPI under /gradio
# Root / continues to serve the React SPA
app = gr.mount_gradio_app(app, demo, path="/gradio", ssr_mode=False)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
