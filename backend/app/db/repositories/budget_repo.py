"""Budget repository for budget operations."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.budget import Budget


class BudgetRepository:
    """Repository for budget operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_budget(self, user_id: UUID) -> Optional[Budget]:
        """
        Get user's budget.

        Args:
            user_id: User ID

        Returns:
            Budget instance or None
        """
        result = await self.db.execute(
            select(Budget).where(Budget.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create_budget(
        self,
        user_id: UUID,
        limit: float,
        period: str = "monthly",
    ) -> Budget:
        """
        Get or create budget for user.

        Args:
            user_id: User ID
            limit: Budget limit
            period: Budget period (daily, weekly, monthly)

        Returns:
            Budget instance
        """
        budget = await self.get_user_budget(user_id)
        if budget:
            return budget

        # Calculate reset_at based on period
        now = datetime.utcnow()
        if period == "daily":
            reset_at = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "weekly":
            days_until_monday = (7 - now.weekday()) % 7
            reset_at = (now + timedelta(days=days_until_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # monthly
            if now.month == 12:
                reset_at = datetime(now.year + 1, 1, 1)
            else:
                reset_at = datetime(now.year, now.month + 1, 1)

        budget = Budget(
            user_id=user_id,
            limit=limit,
            period=period,
            current_spend=0.0,
            reset_at=reset_at,
        )
        self.db.add(budget)
        await self.db.flush()
        return budget

    async def get_current_period_spend(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> float:
        """
        Calculate current period spend from request logs.

        Args:
            user_id: User ID
            start_date: Period start date
            end_date: Period end date

        Returns:
            Total spend in period
        """
        from app.db.models.request_log import RequestLog
        from sqlalchemy import func, and_

        result = await self.db.execute(
            select(func.sum(RequestLog.cost_usd))
            .where(
                and_(
                    RequestLog.user_id == user_id,
                    RequestLog.request_timestamp >= start_date,
                    RequestLog.request_timestamp <= end_date,
                )
            )
        )
        return float(result.scalar() or 0)

    async def update_spend(self, user_id: UUID, amount: float) -> Budget:
        """
        Update budget spend.

        Args:
            user_id: User ID
            amount: Amount to add to current spend

        Returns:
            Updated Budget instance
        """
        budget = await self.get_user_budget(user_id)
        if not budget:
            raise ValueError(f"Budget not found for user {user_id}")

        budget.current_spend += amount
        budget.updated_at = datetime.utcnow()
        await self.db.flush()
        return budget

    async def reset_budget(self, user_id: UUID) -> Budget:
        """
        Reset budget for new period.

        Args:
            user_id: User ID

        Returns:
            Updated Budget instance
        """
        budget = await self.get_user_budget(user_id)
        if not budget:
            raise ValueError(f"Budget not found for user {user_id}")

        # Calculate new reset_at
        now = datetime.utcnow()
        if budget.period == "daily":
            budget.reset_at = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif budget.period == "weekly":
            days_until_monday = (7 - now.weekday()) % 7
            budget.reset_at = (now + timedelta(days=days_until_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # monthly
            if now.month == 12:
                budget.reset_at = datetime(now.year + 1, 1, 1)
            else:
                budget.reset_at = datetime(now.year, now.month + 1, 1)

        budget.current_spend = 0.0
        budget.updated_at = datetime.utcnow()
        await self.db.flush()
        return budget

