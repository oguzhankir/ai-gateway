"""Audit service for logging requests."""

from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.request_repo import RequestRepository
from app.db.session import AsyncSessionLocal
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AuditService:
    """Service for audit logging."""

    def __init__(self, db: AsyncSession):
        # Keep db reference for synchronous operations, but create new session for async tasks
        self._db = db

    async def log_request(
        self,
        user_id: UUID,
        provider: str,
        model: str,
        messages: list,
        completion: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        cost_usd: float,
        duration_ms: int,
        cache_hit: bool = False,
        pii_detected: bool = False,
        pii_entities: list = None,
        status: str = "completed",
        error_message: str = None,
        guardrail_violations: list = None,
    ):
        """
        Log a request to the database.

        Args:
            user_id: User ID
            provider: Provider name
            model: Model name
            messages: Request messages
            completion: Completion text
            prompt_tokens: Prompt token count
            completion_tokens: Completion token count
            total_tokens: Total token count
            cost_usd: Cost in USD
            duration_ms: Duration in milliseconds
            cache_hit: Whether cache was hit
            pii_detected: Whether PII was detected
            pii_entities: List of PII entities
            status: Request status
            error_message: Error message if failed
            guardrail_violations: List of guardrail violations
        """
        # Use a separate session for async task to avoid transaction conflicts
        async with AsyncSessionLocal() as db:
            try:
                request_repo = RequestRepository(db)
                request_data = {
                    "user_id": user_id,
                    "request_timestamp": datetime.utcnow(),
                    "provider": provider,
                    "model": model,
                    "messages": messages,
                    "completion": completion,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "cost_usd": cost_usd,
                    "duration_ms": duration_ms,
                    "cache_hit": cache_hit,
                    "pii_detected": pii_detected,
                    "pii_entities": [e.to_dict() if hasattr(e, "to_dict") else e for e in (pii_entities or [])],
                    "status": status,
                    "error_message": error_message,
                    "guardrail_violations": guardrail_violations,
                }

                request_log = await request_repo.create(request_data)
                await db.commit()
                return request_log
            except Exception as e:
                logger.error(f"Failed to log request: {e}")
                await db.rollback()
                return None

