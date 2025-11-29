"""Gateway request/response schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Message(BaseModel):
    """Chat message."""

    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")


class ChatCompletionRequest(BaseModel):
    """Chat completion request."""

    messages: List[Message] = Field(..., description="List of messages")
    model: Optional[str] = Field(None, description="Model name")
    provider: Optional[str] = Field(None, description="Provider name (openai, gemini)")
    detection_mode: Optional[str] = Field("fast", description="PII detection mode (fast, detailed)")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Sampling temperature")
    stream: Optional[bool] = Field(False, description="Enable streaming")


class GatewayResponse(BaseModel):
    """Gateway response."""

    completion: str
    tokens: Dict[str, int] = Field(..., description="Token counts")
    cost: float = Field(..., description="Cost in USD")
    cache_hit: bool = Field(False, description="Whether response was from cache")
    pii_detected: bool = Field(False, description="Whether PII was detected")
    pii_entities: Optional[List[Dict[str, Any]]] = Field(None, description="Detected PII entities")
    duration_ms: int = Field(..., description="Request duration in milliseconds")
    model: str = Field(..., description="Model used")
    provider: str = Field(..., description="Provider used")
    request_id: Optional[str] = Field(None, description="Request ID")


class PIIDetectionRequest(BaseModel):
    """PII detection request."""

    text: str = Field(..., description="Text to analyze")
    mode: Optional[str] = Field("fast", description="Detection mode (fast, detailed)")


class PIIDetectionResponse(BaseModel):
    """PII detection response."""

    entities: List[Dict[str, Any]] = Field(..., description="Detected PII entities")
    mode: str = Field(..., description="Detection mode used")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    count: int = Field(..., description="Number of entities detected")

