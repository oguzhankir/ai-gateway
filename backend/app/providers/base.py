"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator, Optional
from dataclasses import dataclass
from app.core.timeout import timeout_wrapper
from app.core.exceptions import TimeoutException


@dataclass
class ProviderResponse:
    """Provider response."""

    completion: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    cost_usd: float
    provider: str


class BaseProvider(ABC):
    """Base class for LLM providers."""

    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    @abstractmethod
    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> ProviderResponse:
        """
        Complete a chat conversation.

        Args:
            messages: List of message dictionaries
            model: Model name
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            ProviderResponse
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream completion.

        Args:
            messages: List of message dictionaries
            model: Model name
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Yields:
            Chunks of completion text
        """
        pass

    @abstractmethod
    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
    ) -> float:
        """
        Calculate cost for tokens.

        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            model: Model name

        Returns:
            Cost in USD
        """
        pass

    async def complete_with_timeout(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout_seconds: Optional[float] = None,
    ) -> ProviderResponse:
        """
        Complete with timeout wrapper.

        Args:
            messages: List of message dictionaries
            model: Model name
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            timeout_seconds: Timeout in seconds

        Returns:
            ProviderResponse

        Raises:
            TimeoutException: If timeout occurs
        """
        return await timeout_wrapper(
            self.complete(messages, model, max_tokens, temperature),
            timeout_seconds,
        )

