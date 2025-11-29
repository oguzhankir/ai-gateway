"""Embedding provider factory."""

from typing import Optional
from app.config import config_manager
from app.embeddings.base import BaseEmbeddingProvider
from app.embeddings.openai_embeddings import OpenAIEmbeddingProvider
from app.embeddings.gemini_embeddings import GeminiEmbeddingProvider


class EmbeddingProviderFactory:
    """Factory for creating embedding provider instances."""

    _instance: Optional["EmbeddingProviderFactory"] = None
    _provider: Optional[BaseEmbeddingProvider] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_provider(self) -> BaseEmbeddingProvider:
        """
        Get embedding provider instance.

        Returns:
            Embedding provider instance
        """
        if self._provider is None:
            provider_name = config_manager.get("cache.embedding_provider", "openai")
            
            if provider_name == "openai":
                self._provider = OpenAIEmbeddingProvider()
            elif provider_name == "gemini":
                self._provider = GeminiEmbeddingProvider()
            else:
                # Default to OpenAI
                self._provider = OpenAIEmbeddingProvider()

        return self._provider


# Singleton instance
embedding_factory = EmbeddingProviderFactory()

