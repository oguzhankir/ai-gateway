"""Fallback manager for provider failover."""

from typing import List, Dict, Optional
from app.config import config_manager
from app.providers.base import BaseProvider, ProviderResponse
from app.providers.factory import provider_factory
from app.core.exceptions import ProviderException
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FallbackManager:
    """Manager for provider fallback."""

    def __init__(self):
        self._enabled = config_manager.get("fallback.enabled", True)
        self._order = config_manager.get("fallback.order", ["openai", "gemini"])

    async def execute_with_fallback(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> ProviderResponse:
        """
        Execute request with fallback.

        Args:
            messages: List of message dictionaries
            model: Model name (optional, uses provider default if not provided)
            provider: Primary provider name
            max_tokens: Maximum tokens
            temperature: Sampling temperature

        Returns:
            ProviderResponse from first successful provider

        Raises:
            ProviderException: If all providers fail
        """
        if not self._enabled or not provider:
            # No fallback, use primary provider
            provider_instance = provider_factory.get_provider(provider)
            return await provider_instance.complete(messages, model or provider_instance.default_model, max_tokens, temperature)

        # Try providers in order
        providers_to_try = [provider] + [p for p in self._order if p != provider]

        last_error = None
        for provider_name in providers_to_try:
            try:
                provider_instance = provider_factory.get_provider(provider_name)
                
                # Use specified model only if it belongs to this provider, otherwise use provider default
                provider_models = config_manager.get(f"providers.{provider_name}.models", [])
                
                if provider_name == provider:
                    # Original provider - always use specified model (even if it fails, we'll fallback)
                    provider_model = model or config_manager.get(f"providers.{provider_name}.default_model", "gpt-3.5-turbo")
                elif model and model in provider_models:
                    # Fallback provider but model belongs to it - use the model
                    provider_model = model
                else:
                    # Fallback provider - use its default model
                    provider_model = config_manager.get(f"providers.{provider_name}.default_model", "gpt-3.5-turbo")
                
                logger.info(f"Attempting provider: {provider_name} with model: {provider_model}")
                response = await provider_instance.complete(
                    messages,
                    provider_model,
                    max_tokens,
                    temperature,
                )
                
                if provider_name != provider:
                    logger.info(f"Fallback successful: {provider_name}")
                
                return response
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider_name} failed: {e}")
                continue

        # All providers failed
        raise ProviderException(
            f"All providers failed. Last error: {last_error}",
            provider="fallback",
        )


# Singleton instance
fallback_manager = FallbackManager()

