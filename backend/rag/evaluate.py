from __future__ import annotations
import json
from statistics import mean
from typing import List

from backend.rag.retrieve import retrieve
from backend.rag.qa import answer_question

# -----------------------------
# Utility metrics
# -----------------------------

def recall_at_k(gt: List[List[int]], preds: List[List[int]], k: int = 5) -> float:
    """Compute Recall@k: fraction of queries with at least one relevant doc in top-k."""
    return mean([any(pid in preds[i][:k] for pid in gt[i]) for i in range(len(gt))])


def precision_at_k(gt: List[List[int]], preds: List[List[int]], k: int = 5) -> float:
    """Compute Precision@k: average fraction of top-k retrieved docs that are relevant."""
    prec = []
    for i in range(len(gt)):
        hits = sum(1 for pid in preds[i][:k] if pid in gt[i])
        prec.append(hits / k)
    return mean(prec)


def mrr(gt: List[List[int]], preds: List[List[int]], k: int = 10) -> float:
    """Compute Mean Reciprocal Rank (MRR@k)."""
    rr = []
    for i in range(len(gt)):
        rank = next((j + 1 for j, pid in enumerate(preds[i][:k]) if pid in gt[i]), None)
        rr.append(0 if rank is None else 1.0 / rank)
    return mean(rr)


# -----------------------------
# Main evaluation pipeline
# -----------------------------

def main():
    index_dir = "data/index"  # adjust if your FAISS index lives somewhere else
    top_k = 5

    # Load eval set
    with open("eval_set.json", "r") as f:
        eval_data = json.load(f)

    retriever_results, gt_ids = [], []

    for item in eval_data:
        query = item["query"]
        relevant_ids = item["relevant_ids"]  # list of ground-truth passage IDs
        reference_answer = item.get("reference_answer", "")

        # --- Retriever
        hits = retrieve(query, index_dir=index_dir, top_k=top_k)
        retrieved_ids = [h["page"] for h in hits]  # using page as doc ID
        retriever_results.append(retrieved_ids)
        gt_ids.append(relevant_ids)

        # --- Generator (called, but not used for metrics)
        answer, citations, _, _ = answer_question(
            query, session_id=None, top_k=top_k, index_dir=index_dir
        )

        print("Q:", query)
        print("Retrieved IDs:", retrieved_ids)
        print("Answer:", answer)
        print("Reference:", reference_answer)
        print("-" * 60)

    # --- Aggregate retrieval metrics
    print("\n=== Retrieval Metrics ===")
    recall = recall_at_k(gt_ids, retriever_results, k=5)
    precision = precision_at_k(gt_ids, retriever_results, k=5)
    mrr_score = mrr(gt_ids, retriever_results, k=10)

    print("Recall@5:", recall)
    print("Precision@5:", precision)
    print("MRR@10:", mrr_score)

    # --- Retrieval F1
    retrieval_f1 = (
        2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    )

    print("\n=== Retrieval F1 Score ===")
    print("F1 Score:", retrieval_f1)


if __name__ == "__main__":
    main()
