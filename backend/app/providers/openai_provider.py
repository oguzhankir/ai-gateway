"""OpenAI provider implementation."""

import asyncio
from typing import List, Dict, Optional, AsyncGenerator
import tiktoken
from openai import AsyncOpenAI
from openai import APIError

from app.config import config_manager, settings
from app.providers.base import BaseProvider, ProviderResponse
from app.core.exceptions import ProviderException


class OpenAIProvider(BaseProvider):
    """OpenAI provider."""

    def __init__(self):
        super().__init__("openai")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.pricing = config_manager.get("providers.openai.pricing", {})
        self.max_retries = config_manager.get("providers.openai.max_retries", 3)
        self.retry_delay = config_manager.get("providers.openai.retry_delay", 1.0)

    def _count_tokens(self, messages: List[Dict[str, str]], model: str) -> int:
        """Count tokens using tiktoken."""
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")

        tokens_per_message = 3  # Every message follows <|start|>assistant<|message|>
        tokens_per_name = 1  # If there's a name, the role is omitted

        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(encoding.encode(str(value)))
                if key == "name":
                    num_tokens += tokens_per_name

        num_tokens += 3  # Every reply is primed with <|start|>assistant<|message|>
        return num_tokens

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> ProviderResponse:
        """Complete chat completion."""
        for attempt in range(self.max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

                completion = response.choices[0].message.content or ""
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                total_tokens = response.usage.total_tokens

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
            except APIError as e:
                if attempt == self.max_retries - 1:
                    raise ProviderException(
                        f"OpenAI API error: {e}",
                        provider=self.provider_name,
                        status_code=getattr(e, "status_code", None),
                    )
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
            except Exception as e:
                raise ProviderException(
                    f"OpenAI error: {e}",
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
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise ProviderException(
                f"OpenAI streaming error: {e}",
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
        prompt_price = model_pricing.get("prompt", 0.0) / 1000  # Per 1K tokens
        completion_price = model_pricing.get("completion", 0.0) / 1000

        cost = (prompt_tokens * prompt_price) + (completion_tokens * completion_price)
        return cost

