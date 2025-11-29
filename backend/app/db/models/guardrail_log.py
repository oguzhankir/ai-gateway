"""Guardrail log model."""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


class GuardrailLog(Base):
    """Guardrail log model for tracking guardrail violations."""

    __tablename__ = "guardrail_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    request_id = Column(UUID(as_uuid=True), ForeignKey("request_logs.id"), nullable=True, index=True)
    rule_name = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False)  # error, warning, info
    action = Column(String(20), nullable=False)  # block, log, alert
    details = Column(JSONB, nullable=True)  # Additional details about the violation
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

