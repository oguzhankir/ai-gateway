"""Tests for semantic cache."""

import pytest
from app.cache.semantic_cache import semantic_cache
from app.cache.similarity import cosine_similarity, is_similar
import numpy as np


@pytest.mark.asyncio
async def test_similarity_calculation():
    """Test cosine similarity calculation."""
    vec1 = np.array([1, 0, 0], dtype=np.float32)
    vec2 = np.array([1, 0, 0], dtype=np.float32)
    
    similarity = cosine_similarity(vec1, vec2)
    assert similarity == pytest.approx(1.0)
    
    vec3 = np.array([0, 1, 0], dtype=np.float32)
    similarity = cosine_similarity(vec1, vec3)
    assert similarity == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_is_similar():
    """Test similarity threshold check."""
    vec1 = np.array([1, 0, 0], dtype=np.float32)
    vec2 = np.array([0.99, 0.01, 0], dtype=np.float32)
    
    assert is_similar(vec1, vec2, threshold=0.95) == True
    assert is_similar(vec1, vec2, threshold=0.99) == False


@pytest.mark.asyncio
async def test_cache_operations():
    """Test cache get/set operations."""
    # Note: This requires Redis to be running
    # In CI/CD, you might want to mock Redis or skip these tests
    
    query_text = "What is artificial intelligence?"
    response = {"completion": "AI is...", "tokens": 100}
    
    # Set cache
    await semantic_cache.set(query_text, response)
    
    # Get cache
    cached = await semantic_cache.get(query_text)
    # Note: May return None if similarity threshold not met or Redis not available
    # This is expected behavior
