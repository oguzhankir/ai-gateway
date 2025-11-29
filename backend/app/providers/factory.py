"""Provider factory."""

from typing import Optional, Dict
from app.providers.base import BaseProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.gemini_provider import GeminiProvider


class ProviderFactory:
    """Factory for creating provider instances."""

    _instance: Optional["ProviderFactory"] = None
    _providers: Dict[str, BaseProvider] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_provider(self, provider_name: str) -> BaseProvider:
        """
        Get provider instance.

        Args:
            provider_name: Name of provider (openai, gemini)

        Returns:
            Provider instance
        """
        if provider_name not in self._providers:
            if provider_name == "openai":
                self._providers[provider_name] = OpenAIProvider()
            elif provider_name == "gemini":
                self._providers[provider_name] = GeminiProvider()
            else:
                raise ValueError(f"Unknown provider: {provider_name}")

        return self._providers[provider_name]


# Singleton instance
provider_factory = ProviderFactory()

