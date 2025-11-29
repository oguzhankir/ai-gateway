"""Analytics endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.dependencies import get_db, get_current_user, get_admin_user
from app.db.models.user import User
from app.schemas.analytics import OverviewStats, ProviderStats, UserStats, TimelineStats, RecentRequest
from app.services.analytics_service import AnalyticsService


def to_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Convert timezone-aware datetime to naive UTC datetime."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        # Convert to UTC and remove timezone info
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

router = APIRouter()


@router.get("/overview", response_model=OverviewStats)
async def get_overview(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get overview statistics."""
    service = AnalyticsService(db)
    return await service.get_overview_stats(
        to_naive_utc(start_date), to_naive_utc(end_date), user.id
    )


@router.get("/providers", response_model=list[ProviderStats])
async def get_provider_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get provider statistics."""
    service = AnalyticsService(db)
    return await service.get_provider_stats(to_naive_utc(start_date), to_naive_utc(end_date))


@router.get("/users", response_model=list[UserStats])
async def get_user_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db),
    is_admin: bool = Depends(get_admin_user),
):
    """Get user statistics (admin only)."""
    service = AnalyticsService(db)
    return await service.get_user_stats(to_naive_utc(start_date), to_naive_utc(end_date), limit)


@router.get("/timeline", response_model=list[TimelineStats])
async def get_timeline(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    granularity: str = Query("hour", regex="^(hour|day|week|month)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get timeline statistics."""
    service = AnalyticsService(db)
    return await service.get_timeline_stats(
        to_naive_utc(start_date), to_naive_utc(end_date), granularity, user.id
    )


@router.get("/recent", response_model=list[RecentRequest])
async def get_recent_requests(
    limit: int = Query(10, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get recent requests."""
    service = AnalyticsService(db)
    return await service.get_recent_requests(user.id, limit)


@router.get("/live")
async def get_live_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get live/real-time statistics."""
    service = AnalyticsService(db)
    return await service.get_live_stats()

