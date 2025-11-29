"""Similarity calculation utilities."""

import numpy as np
from typing import Union, List


def cosine_similarity(vec1: Union[np.ndarray, List[float]], vec2: Union[np.ndarray, List[float]]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score (0-1)
    """
    vec1 = np.array(vec1, dtype=np.float32)
    vec2 = np.array(vec2, dtype=np.float32)

    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    similarity = dot_product / (norm1 * norm2)
    return float(similarity)


def is_similar(
    vec1: Union[np.ndarray, List[float]],
    vec2: Union[np.ndarray, List[float]],
    threshold: float = 0.95,
) -> bool:
    """
    Check if two vectors are similar based on threshold.

    Args:
        vec1: First vector
        vec2: Second vector
        threshold: Similarity threshold (default 0.95)

    Returns:
        True if similar, False otherwise
    """
    similarity = cosine_similarity(vec1, vec2)
    return similarity >= threshold

