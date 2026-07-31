from langchain_chroma import Chroma
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
from config.config import *
import re

from src.embeddings.embedding import embedding_model


def tokenize(text):
    return re.findall(r"[A-Za-z0-9\-\.]+", text.lower())


def make_key(doc):
    metadata = doc.metadata
    return (
        metadata["source"],
        metadata.get("sheet"),
        metadata["chunk_id"],
    )


class HybridRetriever:
    def __init__(self):
        self.vector_store = None
        self.documents = None
        self.metadatas = None
        self.ids = None
        self.bm25 = None

    def load_vector_db(self, chroma_dir, collection_name=COLLECTION_NAME):
        self.vector_store = Chroma(
            persist_directory=str(chroma_dir),
            collection_name=collection_name,
            embedding_function=embedding_model,
        )

        all_docs = self.vector_store.get(include=["documents", "metadatas"])

        self.documents = all_docs["documents"]
        self.metadatas = all_docs["metadatas"]
        self.ids = all_docs["ids"]

        tokenized_docs = [tokenize(doc) for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized_docs)

        return self.vector_store

    def bm25_retrieve(self, query, k=BM25_TOP_K):
        tokenized_query = tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:k]

        results = []
        for i in top_indices:
            results.append({
                "content": self.documents[i],
                "metadata": self.metadatas[i],
                "id": self.ids[i],
                "bm25_score": scores[i]
            })

        return results

    def dense_retrieve(self, query, k=DENSE_TOP_K):
        return self.vector_store.similarity_search_with_score(
            query=query,
            k=k
        )

    # main hybrid retrieval
    def hybrid_retrieve(self, query):
        combined = {}

        dense_results = self.dense_retrieve(query)
        bm25_results = self.bm25_retrieve(query)

        for doc, dense_score in dense_results:
            key = make_key(doc)
            if key not in combined:
                combined[key] = {"document": doc, "dense_score": dense_score, "bm25_score": None}
            else:
                if combined[key]["dense_score"] is None or dense_score < combined[key]["dense_score"]:
                    combined[key]["dense_score"] = dense_score

        for result in bm25_results:
            key = make_key(Document(page_content=result["content"], metadata=result["metadata"]))
            if key not in combined:
                combined[key] = {
                    "document": Document(page_content=result["content"], metadata=result["metadata"]),
                    "dense_score": None,
                    "bm25_score": result["bm25_score"]
                }
            else:
                current = combined[key]["bm25_score"]
                if current is None or result["bm25_score"] > current:
                    combined[key]["bm25_score"] = result["bm25_score"]

        return list(combined.values())
