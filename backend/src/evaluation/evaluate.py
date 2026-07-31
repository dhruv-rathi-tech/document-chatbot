from config.config import *

def evaluate_retrieval(retrieval_results):
    filtered_results = []

    for i, result in enumerate(retrieval_results, start=1):
        dense_score = result["dense_score"]
        bm25_score = result["bm25_score"]

        dense_pass = (dense_score is not None and dense_score <= DENSE_DISTANCE_THRESHOLD)
        bm25_pass = (bm25_score is not None and bm25_score >= BM25_SCORE_THRESHOLD)

        if dense_pass or bm25_pass:
            filtered_results.append(result)

    return filtered_results


def evaluate_reranker(reranked_results):
    filtered_results = []

    for i, result in enumerate(reranked_results, start=1):
        reranked_score = result["cross_score"]

        if reranked_score >= RERANKED_SCORE_THRESHOLD:
            filtered_results.append(result)

    return filtered_results
