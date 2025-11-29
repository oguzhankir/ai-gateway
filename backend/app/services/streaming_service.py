"""Streaming service for SSE streaming."""

from typing import List, Dict, Optional, AsyncGenerator
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.pii.detector import pii_detector
from app.pii.masker import pii_masker
from app.providers.factory import provider_factory
from app.providers.router import ab_router
from app.config import config_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class StreamingService:
    """Service for streaming completions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def stream_completion(
        self,
        user_id: UUID,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        detection_mode: str = "fast",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream completion with SSE.

        Args:
            user_id: User ID
            messages: List of messages
            model: Model name
            provider: Provider name
            detection_mode: PII detection mode
            max_tokens: Maximum tokens
            temperature: Sampling temperature

        Yields:
            SSE formatted chunks
        """
        session_id = ""
        full_completion = ""

        try:
            # PII detection and masking on input
            text_content = " ".join([msg.get("content", "") for msg in messages])
            pii_result = pii_detector.detect(text_content, detection_mode)
            
            if pii_result.entities and config_manager.get("pii.masking.enabled", True):
                masked_text, session_id = await pii_masker.mask(text_content, pii_result.entities)
                messages = [
                    {**msg, "content": masked_text if i == len(messages) - 1 else msg.get("content", "")}
                    for i, msg in enumerate(messages)
                ]

            # Determine provider and model
            if not provider:
                provider, model = ab_router.route_request()

            if not model:
                model = config_manager.get(f"providers.{provider}.default_model", "gpt-3.5-turbo")

            # Get provider and stream
            provider_instance = provider_factory.get_provider(provider)
            
            async for chunk in provider_instance.stream(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            ):
                full_completion += chunk
                
                # Unmask chunk if needed
                if session_id:
                    chunk = await pii_masker.unmask(chunk, session_id)
                
                # Yield SSE format
                yield f"data: {chunk}\n\n"

            # Yield completion
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: [ERROR] {str(e)}\n\n"

