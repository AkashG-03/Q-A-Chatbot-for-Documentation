# backend/rag/rerank.py
from __future__ import annotations

import numpy as np
from typing import List, Dict, Any
from collections import defaultdict


def rerank_multi_query_results(
    query_results: Dict[str, List[Dict[str, Any]]],
    top_k: int = 4
) -> List[Dict[str, Any]]:
    """
    Re-rank results from multiple query paraphrases
    Uses frequency and average score to determine final ranking
    
    Args:
        query_results: Dict mapping query -> list of results
        top_k: Number of documents to return
    
    Returns:
        List of re-ranked documents
    """
    # Collect all unique documents with their scores and frequencies
    doc_scores = defaultdict(list)  # doc_key -> list of scores
    doc_metadata = {}  # doc_key -> document metadata
    
    for query, results in query_results.items():
        for result in results:
            # Create unique key for document (source + page + text hash)
            doc_key = f"{result['source']}|{result['page']}|{hash(result['text'][:100])}"
            doc_scores[doc_key].append(result['score'])
            doc_metadata[doc_key] = result
    
    # Calculate final scores based on frequency and average score
    final_scores = []
    
    for doc_key, scores in doc_scores.items():
        frequency = len(scores)  # How many queries retrieved this doc
        avg_score = np.mean(scores)  # Average retrieval score
        max_score = max(scores)  # Best retrieval score
        
        # Combined score: frequency boost + quality score
        frequency_boost = min(frequency / len(query_results), 1.0)  # Normalize by number of queries
        final_score = 0.3 * frequency_boost + 0.4 * avg_score + 0.3 * max_score
        
        doc_with_score = doc_metadata[doc_key].copy()
        doc_with_score['final_score'] = final_score
        doc_with_score['frequency'] = frequency
        doc_with_score['avg_score'] = avg_score
        
        final_scores.append(doc_with_score)
    
    # Sort by final score and return top-k
    final_scores.sort(key=lambda x: x['final_score'], reverse=True)
    
    print(f"Multi-query reranking: {len(final_scores)} unique docs from {len(query_results)} queries")
    for i, doc in enumerate(final_scores[:top_k]):
        print(f"  {i+1}. {doc['source']} p.{doc['page']} - Final: {doc['final_score']:.3f} "
              f"(freq: {doc['frequency']}, avg: {doc['avg_score']:.3f})")
    
    return final_scores[:top_k]


def calculate_mmr(
    query_embedding: np.ndarray,
    candidate_embeddings: List[np.ndarray],
    candidate_docs: List[Dict[str, Any]],
    lambda_param: float = 0.7,
    top_k: int = 4
) -> List[Dict[str, Any]]:
    """
    Apply Maximal Marginal Relevance (MMR) to balance relevance and diversity
    
    Args:
        query_embedding: The query embedding vector
        candidate_embeddings: List of document embedding vectors
        candidate_docs: List of document metadata
        lambda_param: Balance between relevance (1.0) and diversity (0.0)
        top_k: Number of documents to return
    
    Returns:
        List of re-ranked documents
    """
    if not candidate_docs or len(candidate_docs) != len(candidate_embeddings):
        return candidate_docs[:top_k]
    
    selected_docs = []
    selected_embeddings = []
    remaining_docs = list(enumerate(zip(candidate_docs, candidate_embeddings)))
    
    while len(selected_docs) < top_k and remaining_docs:
        if not selected_docs:
            # First document: highest similarity to query
            similarities = [
                np.dot(query_embedding, emb) / (np.linalg.norm(query_embedding) * np.linalg.norm(emb))
                for _, (_, emb) in remaining_docs
            ]
            best_idx = max(range(len(similarities)), key=lambda i: similarities[i])
            idx, (doc, emb) = remaining_docs.pop(best_idx)
        else:
            # MMR calculation for remaining documents
            mmr_scores = []
            
            for i, (_, (doc, emb)) in enumerate(remaining_docs):
                # Relevance: similarity to query
                query_sim = np.dot(query_embedding, emb) / (np.linalg.norm(query_embedding) * np.linalg.norm(emb))
                
                # Diversity: maximum similarity to already selected documents
                max_selected_sim = 0
                for selected_emb in selected_embeddings:
                    sim = np.dot(emb, selected_emb) / (np.linalg.norm(emb) * np.linalg.norm(selected_emb))
                    max_selected_sim = max(max_selected_sim, sim)
                
                # MMR score
                mmr_score = lambda_param * query_sim - (1 - lambda_param) * max_selected_sim
                mmr_scores.append(mmr_score)
            
            # Select document with highest MMR score
            best_idx = max(range(len(mmr_scores)), key=lambda i: mmr_scores[i])
            idx, (doc, emb) = remaining_docs.pop(best_idx)
        
        selected_docs.append(doc)
        selected_embeddings.append(emb)
    
    return selected_docs


def apply_cross_encoder_reranking(
    query: str,
    documents: List[Dict[str, Any]],
    top_k: int = 4
) -> List[Dict[str, Any]]:
    """
    Apply cross-encoder re-ranking for more precise relevance scoring
    This is more computationally expensive but more accurate
    
    Args:
        query: The search query
        documents: List of candidate documents
        top_k: Number of documents to return
    
    Returns:
        Re-ranked list of documents
    
    Note: Requires sentence-transformers with cross-encoder models
    """
    try:
        from sentence_transformers import CrossEncoder
        
        # Load a medical/clinical cross-encoder if available
        # For now, use a general-purpose model
        model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-2-v2')
        
        # Prepare query-document pairs
        pairs = [(query, doc['text'][:512]) for doc in documents]  # Limit text length
        
        # Get relevance scores
        scores = model.predict(pairs)
        
        # Combine with original scores
        for i, doc in enumerate(documents):
            doc['cross_encoder_score'] = float(scores[i])
            # Weighted combination of original and cross-encoder scores
            doc['combined_score'] = 0.6 * doc.get('score', 0.5) + 0.4 * doc['cross_encoder_score']
        
        # Re-sort by combined score
        documents.sort(key=lambda x: x['combined_score'], reverse=True)
        
        print(f"Cross-encoder reranking applied to {len(documents)} documents")
        
    except ImportError:
        print("Cross-encoder model not available, skipping cross-encoder reranking")
    except Exception as e:
        print(f"Cross-encoder reranking failed: {e}")
    
    return documents[:top_k]
