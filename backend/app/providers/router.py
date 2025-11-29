"""A/B testing router for providers."""

import random
from typing import Optional, Tuple
from app.config import config_manager


class ABRouter:
    """Router for A/B testing."""

    def __init__(self):
        self._enabled = config_manager.get("ab_testing.enabled", False)
        self._variants = config_manager.get("ab_testing.variants", [])

    def route_request(self) -> Tuple[str, str]:
        """
        Route request to provider/model based on A/B test configuration.

        Returns:
            Tuple of (provider_name, model_name)
        """
        if not self._enabled or not self._variants:
            # Return default
            default_provider = config_manager.get("providers.openai.enabled", True) and "openai" or "gemini"
            default_model = config_manager.get(f"providers.{default_provider}.default_model", "gpt-3.5-turbo")
            return default_provider, default_model

        # Select variant based on percentage
        rand = random.random() * 100
        cumulative = 0

        for variant in self._variants:
            cumulative += variant.get("percentage", 0)
            if rand <= cumulative:
                provider = variant.get("provider", "openai")
                model = variant.get("model", "gpt-3.5-turbo")
                return provider, model

        # Fallback to first variant
        if self._variants:
            variant = self._variants[0]
            return variant.get("provider", "openai"), variant.get("model", "gpt-3.5-turbo")

        # Ultimate fallback
        return "openai", "gpt-3.5-turbo"


# Singleton instance
ab_router = ABRouter()

