"""Google Gemini provider implementation."""

from typing import List, Dict, Optional, AsyncGenerator
import google.generativeai as genai

from app.config import config_manager, settings
from app.providers.base import BaseProvider, ProviderResponse
from app.core.exceptions import ProviderException


class GeminiProvider(BaseProvider):
    """Google Gemini provider."""

    def __init__(self):
        super().__init__("gemini")
        genai.configure(api_key=settings.gemini_api_key)
        self.pricing = config_manager.get("providers.gemini.pricing", {})
        self.max_retries = config_manager.get("providers.gemini.max_retries", 3)

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> ProviderResponse:
        """Complete chat completion."""
        try:
            # Convert messages format for Gemini
            gemini_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "system":
                    # Gemini doesn't have system messages, prepend to first user message
                    if gemini_messages:
                        gemini_messages[-1] += f"\n{content}"
                    else:
                        gemini_messages.append({"role": "user", "parts": [content]})
                else:
                    gemini_role = "user" if role == "user" else "model"
                    gemini_messages.append({"role": gemini_role, "parts": [content]})

            # Configure generation
            generation_config = {}
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens
            if temperature:
                generation_config["temperature"] = temperature

            # Create model and generate
            model_instance = genai.GenerativeModel(model)
            response = await model_instance.generate_content_async(
                gemini_messages,
                generation_config=generation_config,
            )

            completion = response.text or ""
            
            # Get token counts from response
            prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) if hasattr(response, "usage_metadata") else 0
            completion_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) if hasattr(response, "usage_metadata") else 0
            total_tokens = prompt_tokens + completion_tokens

            cost = self.calculate_cost(prompt_tokens, completion_tokens, model)

            return ProviderResponse(
                completion=completion,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                model=model,
                cost_usd=cost,
                provider=self.provider_name,
            )
        except Exception as e:
            raise ProviderException(
                f"Gemini API error: {e}",
                provider=self.provider_name,
            )

    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion."""
        try:
            # Convert messages format for Gemini
            gemini_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "system":
                    if gemini_messages:
                        gemini_messages[-1] += f"\n{content}"
                    else:
                        gemini_messages.append({"role": "user", "parts": [content]})
                else:
                    gemini_role = "user" if role == "user" else "model"
                    gemini_messages.append({"role": gemini_role, "parts": [content]})

            generation_config = {}
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens
            if temperature:
                generation_config["temperature"] = temperature

            model_instance = genai.GenerativeModel(model)
            response = await model_instance.generate_content_async(
                gemini_messages,
                generation_config=generation_config,
                stream=True,
            )

            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise ProviderException(
                f"Gemini streaming error: {e}",
                provider=self.provider_name,
            )

    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
    ) -> float:
        """Calculate cost."""
        model_pricing = self.pricing.get(model, {})
        prompt_price = model_pricing.get("prompt", 0.0) / 1000
        completion_price = model_pricing.get("completion", 0.0) / 1000

        cost = (prompt_tokens * prompt_price) + (completion_tokens * completion_price)
        return cost

