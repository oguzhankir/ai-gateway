"""Semantic cache using Redis vector search."""

import json
from typing import Optional, Dict, Any
import numpy as np
import redis.asyncio as aioredis

from app.config import config_manager, settings
from app.embeddings.factory import embedding_factory
from app.cache.similarity import cosine_similarity
from app.core.exceptions import CacheException
from app.utils.logger import get_logger


class SemanticCache:
    """Semantic cache using Redis vector search."""

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self._enabled = config_manager.get("cache.enabled", True)
        self._ttl = config_manager.get("cache.ttl", 3600)
        self._similarity_threshold = config_manager.get("cache.similarity_threshold", 0.95)
        self._index_name = config_manager.get("cache.index_name", "semantic_cache")
        self._vector_dimension = config_manager.get("cache.vector_dimension", 1536)
        self._embedding_provider = None

    async def initialize(self):
        """Initialize Redis connection and create vector index."""
        if not self._enabled:
            return

        self.redis = await aioredis.from_url(
            settings.redis_url,
            decode_responses=False,
        )

        # Get embedding provider
        self._embedding_provider = embedding_factory.get_provider()

        # Create vector index if it doesn't exist
        try:
            # Check if index exists
            info = await self.redis.ft(self._index_name).info()
            if info:
                return
        except Exception:
            pass

        # Create index with HNSW and cosine similarity
        try:
            await self.redis.execute_command(
                "FT.CREATE",
                self._index_name,
                "ON", "HASH",
                "PREFIX", "1", f"cache:",
                "SCHEMA",
                "vector", "VECTOR", "HNSW", "6", "TYPE", "FLOAT32", "DIM", str(self._vector_dimension), "DISTANCE_METRIC", "COSINE",
                "text", "TEXT",
                "response", "TEXT",
            )
        except Exception as e:
            # Index might already exist
            if "Index already exists" not in str(e):
                raise CacheException(f"Failed to create vector index: {e}")

    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.aclose()

    async def get(self, query_text: str) -> Optional[Dict[str, Any]]:
        """
        Get cached response if similar query exists.

        Args:
            query_text: Query text

        Returns:
            Cached response dictionary or None
        """
        if not self._enabled or not self.redis or not self._embedding_provider:
            return None

        try:
            # Generate query embedding
            embedding_response = await self._embedding_provider.embed(query_text)
            query_vector = embedding_response.embedding.tolist()

            # Simple approach: scan all cache keys and check similarity
            # This is less efficient but works without RediSearch
            cursor = 0
            best_match = None
            best_similarity = 0.0
            
            while True:
                cursor, keys = await self.redis.scan(cursor, match="cache:*", count=100)
                
                for key in keys:
                    try:
                        # Get cached data
                        cached_data = await self.redis.hgetall(key)
                        if not cached_data:
                            continue
                            
                        cached_text = cached_data.get(b"text", b"").decode() if isinstance(cached_data.get(b"text"), bytes) else cached_data.get("text", "")
                        cached_response = cached_data.get(b"response", b"").decode() if isinstance(cached_data.get(b"response"), bytes) else cached_data.get("response", "")
                        vector_data = cached_data.get(b"vector", b"") if isinstance(cached_data.get(b"vector"), bytes) else cached_data.get("vector", b"")
                        
                        if not vector_data or not cached_response:
                            continue
                            
                        # Calculate similarity
                        cached_vector = np.frombuffer(vector_data, dtype=np.float32)
                        similarity = cosine_similarity(query_vector, cached_vector.tolist())
                        
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_match = cached_response
                    except Exception as e:
                        # Skip invalid cache entries
                        continue
                
                if cursor == 0:
                    break
            
            # Check if best match meets threshold
            if best_match and best_similarity >= self._similarity_threshold:
                return json.loads(best_match)

            return None
        except Exception as e:
            # Log error but don't fail request
            logger = get_logger(__name__)
            logger.warning(f"Cache get error: {e}")
            return None

    async def set(self, query_text: str, response: Dict[str, Any]) -> None:
        """
        Cache a response.

        Args:
            query_text: Query text
            response: Response to cache
        """
        if not self._enabled or not self.redis or not self._embedding_provider:
            return

        try:
            # Generate embedding
            embedding_response = await self._embedding_provider.embed(query_text)
            vector = embedding_response.embedding

            # Create cache key
            import hashlib
            cache_key = f"cache:{hashlib.md5(query_text.encode()).hexdigest()}"

            # Store in Redis hash
            await self.redis.hset(
                cache_key,
                mapping={
                    "vector": vector.tobytes(),
                    "text": query_text,
                    "response": json.dumps(response),
                }
            )

            # Set TTL
            await self.redis.expire(cache_key, self._ttl)
        except Exception as e:
            # Log error but don't fail request
            print(f"Cache set error: {e}")


# Singleton instance
semantic_cache = SemanticCache()

