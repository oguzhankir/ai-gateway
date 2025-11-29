"""Request repository for database operations."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.request_log import RequestLog


class RequestRepository:
    """Repository for request log operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, request_data: dict) -> RequestLog:
        """
        Create a new request log entry.

        Args:
            request_data: Request data dictionary

        Returns:
            Created RequestLog instance
        """
        request_log = RequestLog(**request_data)
        self.db.add(request_log)
        await self.db.flush()
        return request_log

    async def get_by_id(self, request_id: UUID) -> Optional[RequestLog]:
        """
        Get request log by ID.

        Args:
            request_id: Request log ID

        Returns:
            RequestLog instance or None
        """
        result = await self.db.execute(
            select(RequestLog).where(RequestLog.id == request_id)
        )
        return result.scalar_one_or_none()

    async def get_recent(
        self,
        user_id: UUID,
        limit: int = 10,
    ) -> List[RequestLog]:
        """
        Get recent requests for a user.

        Args:
            user_id: User ID
            limit: Maximum number of requests to return

        Returns:
            List of RequestLog instances
        """
        result = await self.db.execute(
            select(RequestLog)
            .where(RequestLog.user_id == user_id)
            .order_by(desc(RequestLog.request_timestamp))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_user(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        provider: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[RequestLog]:
        """
        Get requests for a user with filters.

        Args:
            user_id: User ID
            start_date: Start date filter
            end_date: End date filter
            provider: Provider filter
            limit: Maximum number of requests
            offset: Offset for pagination

        Returns:
            List of RequestLog instances
        """
        query = select(RequestLog).where(RequestLog.user_id == user_id)

        if start_date:
            query = query.where(RequestLog.request_timestamp >= start_date)
        if end_date:
            query = query.where(RequestLog.request_timestamp <= end_date)
        if provider:
            query = query.where(RequestLog.provider == provider)

        query = query.order_by(desc(RequestLog.request_timestamp)).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_by_user(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        provider: Optional[str] = None,
    ) -> int:
        """
        Count requests for a user with filters.

        Args:
            user_id: User ID
            start_date: Start date filter
            end_date: End date filter
            provider: Provider filter

        Returns:
            Count of requests
        """
        query = select(func.count(RequestLog.id)).where(RequestLog.user_id == user_id)

        if start_date:
            query = query.where(RequestLog.request_timestamp >= start_date)
        if end_date:
            query = query.where(RequestLog.request_timestamp <= end_date)
        if provider:
            query = query.where(RequestLog.provider == provider)

        result = await self.db.execute(query)
        return result.scalar() or 0

