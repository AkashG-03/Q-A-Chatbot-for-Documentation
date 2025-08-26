# backend/rag/store.py
from __future__ import annotations

import os
import json
from typing import Any, List, Tuple, Dict

import faiss
import numpy as np


# -----------------------------
# Simple Utilities
# -----------------------------

def index_exists(index_dir: str) -> bool:
    """
    Check if a valid index exists.

    Args:
        index_dir: Directory to check for index files

    Returns:
        True if index exists and is valid, False otherwise
    """
    try:
        load_index(index_dir)
        return True
    except FileNotFoundError:
        return False


# -----------------------------
# Core Index I/O
# -----------------------------

def save_index(
    index_dir: str, 
    index: faiss.IndexFlatIP, 
    embeddings: np.ndarray, 
    metadatas: List[Dict[str, Any]]
):
    """
    Save FAISS index, embeddings, and metadata to disk.

    Args:
        index_dir: Directory to store index files
        index: FAISS index object
        embeddings: Embedding vectors corresponding to documents
        metadatas: List of metadata dictionaries for each vector
    """
    os.makedirs(index_dir, exist_ok=True)

    # Save FAISS index
    faiss.write_index(index, os.path.join(index_dir, "index.faiss"))

    # Save embeddings as numpy array
    np.save(os.path.join(index_dir, "embeddings.npy"), embeddings)

    # Save metadata as JSON
    with open(os.path.join(index_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(metadatas, f, ensure_ascii=False, indent=2)


def load_index(index_dir: str) -> Tuple[faiss.IndexFlatIP, np.ndarray, List[Dict[str, Any]]]:
    """
    Load FAISS index, embeddings, and metadata from disk.

    Args:
        index_dir: Directory containing index files

    Returns:
        Tuple of (index, embeddings, metadatas)

    Raises:
        FileNotFoundError: If any of the index files are missing
    """
    index_path = os.path.join(index_dir, "index.faiss")
    embs_path = os.path.join(index_dir, "embeddings.npy")
    meta_path = os.path.join(index_dir, "meta.json")

    # Check if all required files exist
    if not all(os.path.exists(path) for path in [index_path, embs_path, meta_path]):
        raise FileNotFoundError(
            f"Index files not found in {index_dir}. "
            "Please upload and ingest PDFs first."
        )

    # Load files
    index = faiss.read_index(index_path)
    embeddings = np.load(embs_path)

    with open(meta_path, "r", encoding="utf-8") as f:
        metadatas = json.load(f)

    return index, embeddings, metadatas
