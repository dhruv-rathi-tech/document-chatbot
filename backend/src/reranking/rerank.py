from sentence_transformers import CrossEncoder
from config.config import *

reranker = CrossEncoder(RERANK_MODEL)

def rerank(query, retrieval_results, top_k=RERANK_TOP_K):
    pairs = [
        (query, result["document"].page_content)
        for result in retrieval_results
    ]

    scores = reranker.predict(pairs)

    ranked_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )[:top_k]

    reranked_results = []
    for i in ranked_indices:
        result = retrieval_results[i].copy()
        result["cross_score"] = scores[i]
        reranked_results.append(result)

    return reranked_results
