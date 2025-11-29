"""Google Gemini embedding provider."""

from typing import List
import numpy as np
import google.generativeai as genai

from app.config import config_manager, settings
from app.embeddings.base import BaseEmbeddingProvider, EmbeddingResponse


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """Google Gemini embedding provider."""

    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = "embedding-001"

    async def embed(self, text: str) -> EmbeddingResponse:
        """
        Generate embedding using Gemini.

        Args:
            text: Text to embed

        Returns:
            EmbeddingResponse
        """
        # Note: Gemini embedding API may have different interface
        # This is a placeholder implementation
        result = genai.embed_content(
            model=self.model,
            content=text,
            task_type="retrieval_document",
        )

        embedding_array = np.array(result["embedding"], dtype=np.float32)

        return EmbeddingResponse(
            embedding=embedding_array,
            dimensions=len(embedding_array),
            model=self.model,
            tokens=0,  # Gemini may not provide token count
        )

    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResponse]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of EmbeddingResponse instances
        """
        results = []
        for text in texts:
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_document",
            )
            embedding_array = np.array(result["embedding"], dtype=np.float32)
            results.append(
                EmbeddingResponse(
                    embedding=embedding_array,
                    dimensions=len(embedding_array),
                    model=self.model,
                    tokens=0,
                )
            )
        return results

