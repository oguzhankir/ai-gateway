"""OpenAI embedding provider."""

from typing import List
import numpy as np
from openai import AsyncOpenAI

from app.config import config_manager, settings
from app.embeddings.base import BaseEmbeddingProvider, EmbeddingResponse


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embedding provider."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = config_manager.get("cache.embedding_model", "text-embedding-3-small")

    async def embed(self, text: str) -> EmbeddingResponse:
        """
        Generate embedding using OpenAI.

        Args:
            text: Text to embed

        Returns:
            EmbeddingResponse
        """
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )

        embedding_data = response.data[0]
        embedding_array = np.array(embedding_data.embedding, dtype=np.float32)

        return EmbeddingResponse(
            embedding=embedding_array,
            dimensions=len(embedding_array),
            model=self.model,
            tokens=embedding_data.usage.total_tokens if hasattr(embedding_data, "usage") else 0,
        )

    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResponse]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of EmbeddingResponse instances
        """
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
        )

        results = []
        for i, embedding_data in enumerate(response.data):
            embedding_array = np.array(embedding_data.embedding, dtype=np.float32)
            results.append(
                EmbeddingResponse(
                    embedding=embedding_array,
                    dimensions=len(embedding_array),
                    model=self.model,
                    tokens=embedding_data.usage.total_tokens if hasattr(embedding_data, "usage") else 0,
                )
            )

        return results

