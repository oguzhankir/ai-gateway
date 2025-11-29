"""Request log model."""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Integer,
    Float,
    Boolean,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


class RequestLog(Base):
    """Request log model for tracking all API requests."""

    __tablename__ = "request_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    request_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Request details
    provider = Column(String(50), nullable=False, index=True)
    model = Column(String(100), nullable=False)
    messages = Column(JSONB, nullable=True)  # Store messages as JSON
    max_tokens = Column(Integer, nullable=True)
    temperature = Column(Float, nullable=True)
    
    # Response details
    completion = Column(Text, nullable=True)
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    
    # Cost and performance
    cost_usd = Column(Float, default=0.0, nullable=False)
    duration_ms = Column(Integer, nullable=False)
    
    # Cache and PII
    cache_hit = Column(Boolean, default=False, nullable=False)
    pii_detected = Column(Boolean, default=False, nullable=False)
    pii_entities = Column(JSONB, nullable=True)  # List of detected PII entities
    
    # Status
    status = Column(String(50), nullable=False, default="completed")  # completed, failed, blocked
    error_message = Column(Text, nullable=True)
    
    # Guardrails
    guardrail_violations = Column(JSONB, nullable=True)  # List of violations
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="requests")

    # Indexes
    __table_args__ = (
        Index("idx_user_timestamp", "user_id", "request_timestamp"),
        Index("idx_provider_timestamp", "provider", "request_timestamp"),
    )

