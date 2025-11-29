"""Webhook schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class WebhookCreate(BaseModel):
    """Webhook creation request."""

    url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="List of event types to subscribe to")
    secret: Optional[str] = Field(None, description="HMAC secret (auto-generated if not provided)")


class WebhookResponse(BaseModel):
    """Webhook response."""

    id: UUID
    url: str
    events: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

