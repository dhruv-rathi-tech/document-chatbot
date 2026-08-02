# Document Chatbot

A retrieval-augmented chatbot that lets you upload your own documents (PDF, Word, PowerPoint, Excel, or plain text) and ask questions about them. The backend runs a hybrid dense + keyword retrieval pipeline with cross-encoder reranking before generating an answer, and the frontend is a minimal dark-themed chat interface.

## How it works

1. You upload one or more documents through the UI.
2. The backend parses and cleans the text, then splits it into overlapping chunks.
3. Each chunk is embedded and stored in a per-session Chroma vector store.
4. When you ask a question, the retriever pulls candidates two ways — dense vector similarity and BM25 keyword scoring — and merges the results.
5. A cross-encoder reranks the merged candidates against the query, and a threshold-based filter drops anything that isn't a strong enough match.
6. The remaining chunks are passed to Gemini along with the question, and the model answers strictly from that context.

Every upload gets its own session ID and its own isolated vector store, so documents from different sessions never mix.

**API endpoints:**
- `POST /upload` — upload one or more files, returns a session ID and chunk count
- `POST /chat` — ask a question against a session's documents
- `DELETE /session/{session_id}` — deletes a session's files and vector DB from disk

Uploads are restricted to `.pdf`, `.docx`, `.pptx`, `.xlsx`, `.txt`, and `.md`, with a 20MB per-file size cap enforced server-side.

## Project structure

```
.
├── backend/
│   ├── app.py                     # FastAPI app: /upload, /chat, /session endpoints
│   ├── config/
│   │   └── config.py              # paths, model names, chunking + retrieval thresholds
│   ├── src/
│   │   ├── ingestion/
│   │   │   ├── ingest.py          # document loading + chunking
│   │   │   └── clean.py           # text normalization
│   │   ├── embeddings/
│   │   │   └── embedding.py       # sentence-transformers embeddings + Chroma writes
│   │   ├── retrieval/
│   │   │   └── retrieve.py        # hybrid dense + BM25 retriever
│   │   ├── reranking/
│   │   │   └── rerank.py          # cross-encoder reranking
│   │   ├── generation/
│   │   │   └── generate.py        # prompt template + Gemini call
│   │   └── evaluation/
│   │       └── evaluate.py        # score-based filtering for retrieval and reranking
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx                 # top-level layout and session state
    │   ├── api.js                  # fetch wrappers for the backend
    │   └── components/
    │       ├── FileUpload.jsx
    │       ├── ChatMessage.jsx
    │       ├── ChatInput.jsx
    │       ├── AttachButton.jsx
    │       └── TypingIndicator.jsx
    └── package.json
```

## Retrieval pipeline

**Ingestion.** PDFs, Word docs, and PowerPoint files are converted to plain text via MarkItDown; Excel files are parsed sheet by sheet, with each row turned into its own document so tabular data isn't flattened into a wall of text. Everything else is chunked with a recursive character splitter (chunk size and overlap are configurable).

**Retrieval.** Two retrievers run per query — a dense retriever over the Chroma vector store and a BM25 retriever over the same chunk set — and their results are merged by document identity. On overlap, the merge keeps the lower (better) distance for dense scores and the higher (better) score for BM25.

**Filtering and reranking.** Merged candidates first pass through a score threshold on the raw retrieval scores, then a cross-encoder (`BAAI/bge-reranker-base`) reranks the survivors against the query, followed by a second threshold on the reranked scores. If nothing survives at any stage, the API returns an explicit "not enough information" response instead of forcing an answer.

**Generation.** The final context chunks are handed to Gemini (`gemini-2.5-flash`) with a prompt that explicitly restricts it to the provided context, asks it to flag conflicting information rather than silently pick one side, and appends a source list after generation (not something the model writes itself).

## Running it locally

You'll need Python 3.11+, Node 18+, and a free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).

**Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file inside `backend/` with:

```
GOOGLE_API_KEY=your_key_here
```

Then start the server:

```bash
uvicorn app:app --reload --port 8000
```

Visiting `http://localhost:8000/` should return `{"status": "ok", ...}`.

**Frontend**

```bash
cd frontend
npm install
```

Create a `.env` file inside `frontend/` with:

```
VITE_API_URL=http://localhost:8000
```

Then start the dev server:

```bash
npm run dev
```

Open `http://localhost:5173`, upload a document, and start asking questions.

## Sessions and data lifecycle

Each browser tab gets a UUID session on first upload. That session's files and vector store live under `backend/data/sessions/<session_id>/` and are deleted when the user hits "Clear" or closes the tab (best-effort, via `beforeunload`). There's no database or login layer — this is intentionally stateless and disposable, since the goal is quick document Q&A rather than persistent chat history.

## Known limitations

- The embedding model and cross-encoder both need real memory to run comfortably.
- No persistent history across sessions — closing the tab clears everything.
- No authentication — anything you upload is only isolated by session ID, not access-controlled.