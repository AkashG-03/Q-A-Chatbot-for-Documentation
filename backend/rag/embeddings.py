from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

# Global model instance for efficient loading
_model = None


def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Generate embeddings for a list of texts.
    
    Args:
        texts: List of text strings to embed.
        
    Returns:
        numpy array of embeddings with shape (N, D).
    """
    model = get_model()
    vecs = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return vecs.astype("float32")


def get_model():
    """Get or initialize the sentence transformer model."""
    global _model
    if _model is None:
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model
