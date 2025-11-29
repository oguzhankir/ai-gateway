"""Streaming schemas."""

from pydantic import BaseModel
from typing import Optional
from app.schemas.gateway import Message


class StreamingRequest(BaseModel):
    """Streaming request (same as ChatCompletionRequest)."""

    messages: list[Message]
    model: Optional[str] = None
    provider: Optional[str] = None
    detection_mode: Optional[str] = "fast"
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

