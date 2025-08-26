# backend/rag/retrieve.py
from __future__ import annotations

from typing import List, Dict, Any

import faiss
import numpy as np

from backend.rag.embeddings import embed_texts
from backend.rag.store import load_index
from backend.rag.rerank import calculate_mmr, rerank_multi_query_results


# -----------------------------
# Basic Retrieval (Single Query)
# -----------------------------

def retrieve_single_query(
    query: str, 
    index_dir: str, 
    top_k: int = 12,  # Retrieve more for MMR
    similarity_threshold: float = 0.25
) -> List[Dict[str, Any]]:
    """
    Retrieve documents for a single query (used by multi-query retrieval).
    """
    try:
        index, embeddings, metadatas = load_index(index_dir)
    except FileNotFoundError as e:
        raise ValueError(f"No search index found: {e}")

    # Embed query
    qvec = embed_texts([query])  # Shape: (1, D)
    if qvec is None or qvec.size == 0:
        raise ValueError("Query embedding returned empty vector.")

    # Search FAISS index
    search_k = min(top_k * 2, len(metadatas))  # Over-retrieve for MMR
    scores, indices = index.search(qvec, search_k)

    results: List[Dict[str, Any]] = []

    for rank, (idx, score) in enumerate(zip(indices[0], scores[0])):
        if idx == -1:  # No more results
            continue
        if score < similarity_threshold:  # Filter low similarity
            continue

        meta = metadatas[int(idx)]

        # Skip very short chunks
        if len(meta.get("text", "").strip()) < 50:
            continue

        results.append({
            "rank": rank + 1,
            "score": float(score),
            "text": meta["text"],
            "page": meta["page"],
            "source": meta["source"],
            "type": meta.get("type", "text"),  # e.g., text/table
            "embedding": embeddings[int(idx)]
        })

    return results


# -----------------------------
# Advanced Retrieval (MMR + Multi-query)
# -----------------------------

def retrieve(
    query: str, 
    index_dir: str, 
    top_k: int = 4, 
    use_mmr: bool = True, 
    use_multi_query: bool = True
) -> List[Dict[str, Any]]:
    """
    Enhanced retrieve function with MMR and multi-query support.
    """
    if not use_multi_query:
        # ---- Single query retrieval ----
        results = retrieve_single_query(query, index_dir, top_k * 3)

        if use_mmr and results:
            try:
                query_embedding = embed_texts([query])[0]
                candidate_embeddings = [r["embedding"] for r in results]

                results = calculate_mmr(
                    query_embedding=query_embedding,
                    candidate_embeddings=candidate_embeddings,
                    candidate_docs=results,
                    lambda_param=0.7,
                    top_k=top_k
                )
                print(f"MMR applied: Selected {len(results)} diverse documents")

            except Exception as e:
                print(f"MMR failed, using original ranking: {e}")
                results = results[:top_k]
        else:
            results = results[:top_k]

        # Cleanup (remove embeddings)
        for r in results:
            r.pop("embedding", None)
        return results

    # ---- Multi-query retrieval ----
    from backend.rag.llm import generate_query_paraphrases

    print(f"Generating query paraphrases for: '{query[:50]}...'")

    try:
        all_queries = generate_query_paraphrases(query)
        print(f"Generated {len(all_queries)} queries (including original)")

        query_results = {}
        for i, q in enumerate(all_queries):
            print(f"  Query {i+1}: {q[:80]}...")
            results = retrieve_single_query(q, index_dir, top_k * 2)
            query_results[q] = results
            print(f"    Retrieved {len(results)} documents")

        # Combine + rerank
        final_results = rerank_multi_query_results(query_results, top_k * 2)

        # Apply MMR again (optional)
        if use_mmr and final_results:
            try:
                query_embedding = embed_texts([query])[0]
                candidate_embeddings = [embed_texts([r["text"][:512]])[0] for r in final_results]

                final_results = calculate_mmr(
                    query_embedding=query_embedding,
                    candidate_embeddings=candidate_embeddings,
                    candidate_docs=final_results,
                    lambda_param=0.7,
                    top_k=top_k
                )
                print(f"MMR applied to multi-query results: {len(final_results)} diverse documents")

            except Exception as e:
                print(f"MMR failed on multi-query results: {e}")
                final_results = final_results[:top_k]
        else:
            final_results = final_results[:top_k]

        # Debug print
        print(f"Final retrieval: {len(final_results)} documents selected")
        for i, r in enumerate(final_results):
            score_info = f"Score: {r.get('final_score', r.get('score', 0)):.3f}"
            if "frequency" in r:
                score_info += f" (freq: {r['frequency']})"
            type_info = f"[{r.get('type', 'text').upper()}]" if r.get("type") != "text" else ""
            print(f"  {i+1}. {r['source']} p.{r['page']} {type_info} - {score_info}")

        return final_results

    except Exception as e:
        print(f"Multi-query retrieval failed, falling back to single query: {e}")
        # Fallback to single query
        results = retrieve_single_query(query, index_dir, top_k)
        for r in results:
            r.pop("embedding", None)
        return results[:top_k]
