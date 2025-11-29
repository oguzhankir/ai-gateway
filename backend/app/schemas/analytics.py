"""Analytics schemas."""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class OverviewStats(BaseModel):
    """Overview statistics."""

    total_requests: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    total_cost: float
    avg_duration_ms: float
    cache_hits: int
    pii_detections: int


class ProviderStats(BaseModel):
    """Provider statistics."""

    provider: str
    total_requests: int
    total_tokens: int
    total_cost: float
    avg_duration_ms: float


class UserStats(BaseModel):
    """User statistics."""

    user_id: str
    total_requests: int
    total_tokens: int
    total_cost: float
    avg_duration_ms: float


class TimelineStats(BaseModel):
    """Timeline statistics."""

    timestamp: str
    total_requests: int
    total_tokens: int
    total_cost: float
    avg_duration_ms: float


class RecentRequest(BaseModel):
    """Recent request information."""

    id: str
    timestamp: datetime
    provider: str
    model: str
    tokens: int
    cost: float
    duration_ms: int
    cache_hit: bool
    pii_detected: bool
    status: str

