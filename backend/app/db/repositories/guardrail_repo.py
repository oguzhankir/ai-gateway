"""Guardrail log repository for database operations."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.guardrail_log import GuardrailLog


class GuardrailRepository:
    """Repository for guardrail log operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: UUID,
        rule_name: str,
        severity: str,
        action: str,
        request_id: Optional[UUID] = None,
        details: Optional[dict] = None,
    ) -> GuardrailLog:
        """
        Create a new guardrail log entry.

        Args:
            user_id: User ID
            rule_name: Name of the violated rule
            severity: Severity level (error, warning, info)
            action: Action taken (block, log, alert)
            request_id: Associated request ID (optional)
            details: Additional details about the violation

        Returns:
            Created GuardrailLog instance
        """
        guardrail_log = GuardrailLog(
            user_id=user_id,
            request_id=request_id,
            rule_name=rule_name,
            severity=severity,
            action=action,
            details=details or {},
            timestamp=datetime.utcnow(),
        )
        self.db.add(guardrail_log)
        await self.db.flush()
        return guardrail_log

    async def get_recent(
        self,
        user_id: Optional[UUID] = None,
        limit: int = 100,
    ) -> List[GuardrailLog]:
        """
        Get recent guardrail violations.

        Args:
            user_id: User ID (optional, if None returns all users)
            limit: Maximum number of violations to return

        Returns:
            List of GuardrailLog instances
        """
        query = select(GuardrailLog)
        
        if user_id:
            query = query.where(GuardrailLog.user_id == user_id)
        
        query = query.order_by(desc(GuardrailLog.timestamp)).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_rule(
        self,
        rule_name: str,
        user_id: Optional[UUID] = None,
        limit: int = 100,
    ) -> List[GuardrailLog]:
        """
        Get violations by rule name.

        Args:
            rule_name: Name of the rule
            user_id: User ID (optional)
            limit: Maximum number of violations to return

        Returns:
            List of GuardrailLog instances
        """
        query = select(GuardrailLog).where(GuardrailLog.rule_name == rule_name)
        
        if user_id:
            query = query.where(GuardrailLog.user_id == user_id)
        
        query = query.order_by(desc(GuardrailLog.timestamp)).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

