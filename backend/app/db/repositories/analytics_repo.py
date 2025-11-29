"""Analytics repository for aggregated statistics."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import select, func, desc, and_, Integer, Boolean
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.request_log import RequestLog


class AnalyticsRepository:
    """Repository for analytics and statistics operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_total_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Get aggregate statistics.

        Args:
            start_date: Start date filter
            end_date: End date filter
            user_id: Optional user ID filter

        Returns:
            Dictionary with aggregate statistics
        """
        query = select(
            func.count(RequestLog.id).label("total_requests"),
            func.sum(RequestLog.prompt_tokens).label("total_prompt_tokens"),
            func.sum(RequestLog.completion_tokens).label("total_completion_tokens"),
            func.sum(RequestLog.total_tokens).label("total_tokens"),
            func.sum(RequestLog.cost_usd).label("total_cost"),
            func.avg(RequestLog.duration_ms).label("avg_duration_ms"),
            func.sum(func.cast(RequestLog.cache_hit, Integer)).label("cache_hits"),
            func.sum(func.cast(RequestLog.pii_detected, Integer)).label("pii_detections"),
        )

        conditions = []
        if start_date:
            conditions.append(RequestLog.request_timestamp >= start_date)
        if end_date:
            conditions.append(RequestLog.request_timestamp <= end_date)
        if user_id:
            conditions.append(RequestLog.user_id == user_id)

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.db.execute(query)
        row = result.first()

        return {
            "total_requests": row.total_requests or 0,
            "total_prompt_tokens": row.total_prompt_tokens or 0,
            "total_completion_tokens": row.total_completion_tokens or 0,
            "total_tokens": row.total_tokens or 0,
            "total_cost": float(row.total_cost or 0),
            "avg_duration_ms": float(row.avg_duration_ms or 0),
            "cache_hits": row.cache_hits or 0,
            "pii_detections": row.pii_detections or 0,
        }

    async def get_provider_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get statistics grouped by provider.

        Args:
            start_date: Start date filter
            end_date: End date filter

        Returns:
            List of provider statistics dictionaries
        """
        query = select(
            RequestLog.provider,
            func.count(RequestLog.id).label("total_requests"),
            func.sum(RequestLog.total_tokens).label("total_tokens"),
            func.sum(RequestLog.cost_usd).label("total_cost"),
            func.avg(RequestLog.duration_ms).label("avg_duration_ms"),
        )

        conditions = []
        if start_date:
            conditions.append(RequestLog.request_timestamp >= start_date)
        if end_date:
            conditions.append(RequestLog.request_timestamp <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.group_by(RequestLog.provider).order_by(desc("total_requests"))

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "provider": row.provider,
                "total_requests": row.total_requests,
                "total_tokens": row.total_tokens or 0,
                "total_cost": float(row.total_cost or 0),
                "avg_duration_ms": float(row.avg_duration_ms or 0),
            }
            for row in rows
        ]

    async def get_user_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get statistics grouped by user.

        Args:
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum number of users

        Returns:
            List of user statistics dictionaries
        """
        query = select(
            RequestLog.user_id,
            func.count(RequestLog.id).label("total_requests"),
            func.sum(RequestLog.total_tokens).label("total_tokens"),
            func.sum(RequestLog.cost_usd).label("total_cost"),
            func.avg(RequestLog.duration_ms).label("avg_duration_ms"),
        )

        conditions = []
        if start_date:
            conditions.append(RequestLog.request_timestamp >= start_date)
        if end_date:
            conditions.append(RequestLog.request_timestamp <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.group_by(RequestLog.user_id).order_by(desc("total_requests")).limit(limit)

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "user_id": str(row.user_id),
                "total_requests": row.total_requests,
                "total_tokens": row.total_tokens or 0,
                "total_cost": float(row.total_cost or 0),
                "avg_duration_ms": float(row.avg_duration_ms or 0),
            }
            for row in rows
        ]

    async def get_timeline_stats(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str = "hour",
        user_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get time-series statistics.

        Args:
            start_date: Start date
            end_date: End date
            granularity: Time granularity (hour, day, week, month)
            user_id: Optional user ID filter

        Returns:
            List of timeline statistics dictionaries
        """
        # TimescaleDB time_bucket function
        # For PostgreSQL without TimescaleDB, use date_trunc
        if granularity == "hour":
            time_expr = func.date_trunc("hour", RequestLog.request_timestamp)
        elif granularity == "day":
            time_expr = func.date_trunc("day", RequestLog.request_timestamp)
        elif granularity == "week":
            time_expr = func.date_trunc("week", RequestLog.request_timestamp)
        elif granularity == "month":
            time_expr = func.date_trunc("month", RequestLog.request_timestamp)
        else:
            time_expr = func.date_trunc("hour", RequestLog.request_timestamp)

        query = select(
            time_expr.label("time_bucket"),
            func.count(RequestLog.id).label("total_requests"),
            func.sum(RequestLog.total_tokens).label("total_tokens"),
            func.sum(RequestLog.cost_usd).label("total_cost"),
            func.avg(RequestLog.duration_ms).label("avg_duration_ms"),
        )

        conditions = [
            RequestLog.request_timestamp >= start_date,
            RequestLog.request_timestamp <= end_date,
        ]

        if user_id:
            conditions.append(RequestLog.user_id == user_id)

        query = query.where(and_(*conditions))
        query = query.group_by("time_bucket").order_by("time_bucket")

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "timestamp": row.time_bucket.isoformat() if row.time_bucket else None,
                "total_requests": row.total_requests,
                "total_tokens": row.total_tokens or 0,
                "total_cost": float(row.total_cost or 0),
                "avg_duration_ms": float(row.avg_duration_ms or 0),
            }
            for row in rows
        ]

