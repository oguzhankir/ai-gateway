"""Base embedding provider interface."""

from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass
import numpy as np


@dataclass
class EmbeddingResponse:
    """Embedding response."""

    embedding: np.ndarray
    dimensions: int
    model: str
    tokens: int = 0


class BaseEmbeddingProvider(ABC):
    """Base class for embedding providers."""

    @abstractmethod
    async def embed(self, text: str) -> EmbeddingResponse:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            EmbeddingResponse
        """
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResponse]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of EmbeddingResponse instances
        """
        pass

