"""Analytics service for statistics and reporting."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.analytics_repo import AnalyticsRepository
from app.db.repositories.request_repo import RequestRepository
from app.schemas.analytics import (
    OverviewStats,
    ProviderStats,
    UserStats,
    TimelineStats,
    RecentRequest,
)


class AnalyticsService:
    """Service for analytics and statistics."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics_repo = AnalyticsRepository(db)
        self.request_repo = RequestRepository(db)

    async def get_overview_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[UUID] = None,
    ) -> OverviewStats:
        """Get overview statistics."""
        stats = await self.analytics_repo.get_total_stats(start_date, end_date, user_id)
        return OverviewStats(**stats)

    async def get_provider_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ProviderStats]:
        """Get provider statistics."""
        stats = await self.analytics_repo.get_provider_stats(start_date, end_date)
        return [ProviderStats(**s) for s in stats]

    async def get_user_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[UserStats]:
        """Get user statistics."""
        stats = await self.analytics_repo.get_user_stats(start_date, end_date, limit)
        return [UserStats(**s) for s in stats]

    async def get_timeline_stats(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str = "hour",
        user_id: Optional[UUID] = None,
    ) -> List[TimelineStats]:
        """Get timeline statistics."""
        stats = await self.analytics_repo.get_timeline_stats(
            start_date, end_date, granularity, user_id
        )
        return [TimelineStats(**s) for s in stats]

    async def get_recent_requests(
        self,
        user_id: Optional[UUID] = None,
        limit: int = 10,
    ) -> List[RecentRequest]:
        """Get recent requests."""
        # Use the existing session (from get_db dependency)
        # This is read-only, so it should work fine within the transaction
        if user_id:
            requests = await self.request_repo.get_recent(user_id, limit)
        else:
            # Get from all users - need to modify query to get all
            from app.db.models.request_log import RequestLog
            from sqlalchemy import select, desc
            query = select(RequestLog).order_by(desc(RequestLog.request_timestamp)).limit(limit)
            result = await self.db.execute(query)
            requests = result.scalars().all()

        return [
            RecentRequest(
                id=str(r.id),
                timestamp=r.request_timestamp,
                provider=r.provider,
                model=r.model,
                tokens=r.total_tokens,
                cost=r.cost_usd,
                duration_ms=r.duration_ms,
                cache_hit=r.cache_hit,
                pii_detected=r.pii_detected,
                status=r.status,
            )
            for r in requests
        ]

    async def get_live_stats(self) -> dict:
        """Get live/real-time statistics."""
        # Get stats for last hour
        end_date = datetime.utcnow()
        start_date = datetime.utcnow().replace(hour=end_date.hour - 1 if end_date.hour > 0 else 23)

        stats = await self.analytics_repo.get_total_stats(start_date, end_date)
        return stats

