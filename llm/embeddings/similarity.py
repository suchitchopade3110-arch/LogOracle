# llm/embeddings/similarity.py
"""
Shared embedding + cosine similarity utility.
Used by:
  - intent_gap.py     (intent embed vs diff embed)
  - predictive_warning.py (Thaariha imports this)
  - multi-log correlation (Suchit's correlation engine)

Model: all-MiniLM-L6-v2 — fast, small, good enough for code+log similarity.
"""
import numpy as np
from typing import List, Union

_model = None

def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed(text: str) -> np.ndarray:
    """Encode single string → embedding vector."""
    return get_model().encode(text, convert_to_numpy=True)


def embed_batch(texts: List[str]) -> List[np.ndarray]:
    """Encode list of strings → list of embedding vectors. Faster than one-by-one."""
    return get_model().encode(texts, convert_to_numpy=True)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Cosine similarity between two vectors.
    Returns float in [-1, 1]. Higher = more similar.
    """
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    """
    Cosine distance = 1 - cosine_similarity.
    Used for intent-gap scoring (higher distance = bigger gap).
    """
    return 1.0 - cosine_similarity(a, b)


def most_similar(query: str, candidates: List[str], threshold: float = 0.65):
    """
    Find most similar candidate string to query.
    Returns (best_match_str, score) or (None, 0.0) if below threshold.
    """
    if not candidates:
        return None, 0.0

    q_embed = embed(query)
    c_embeds = embed_batch(candidates)

    best_score = 0.0
    best_idx = -1

    for i, c_embed in enumerate(c_embeds):
        score = cosine_similarity(q_embed, c_embed)
        if score > best_score:
            best_score = score
            best_idx = i

    if best_score >= threshold:
        return candidates[best_idx], best_score
    return None, best_score
