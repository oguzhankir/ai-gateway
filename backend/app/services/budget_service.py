"""Budget service for managing user spending limits."""

from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.budget_repo import BudgetRepository
from app.core.exceptions import BudgetExceededException
from app.config import config_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BudgetService:
    """Service for budget management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.budget_repo = BudgetRepository(db)
        self._enabled = config_manager.get("budget.enabled", True)
        self._default_limit = config_manager.get("budget.default_limit", 1000.0)
        self._default_period = config_manager.get("budget.default_period", "monthly")
        self._alert_thresholds = config_manager.get("budget.alert_thresholds", [0.5, 0.75, 0.9])

    async def check_budget(self, user_id: UUID, cost: float) -> bool:
        """
        Check if user can spend the amount.

        Args:
            user_id: User ID
            cost: Cost to check

        Returns:
            True if within budget, False otherwise

        Raises:
            BudgetExceededException: If budget exceeded
        """
        if not self._enabled:
            return True

        # Use a separate session to avoid nested transaction issues
        from app.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            try:
                from app.db.repositories.budget_repo import BudgetRepository
                budget_repo = BudgetRepository(db)
                
                budget = await budget_repo.get_user_budget(user_id)
                if not budget:
                    # Create default budget
                    budget = await budget_repo.get_or_create_budget(
                        user_id,
                        self._default_limit,
                        self._default_period,
                    )
                    await db.commit()

                # Check if period has reset
                if datetime.utcnow() >= budget.reset_at:
                    await budget_repo.reset_budget(user_id)
                    await db.commit()
                    # Re-fetch updated budget
                    budget = await budget_repo.get_user_budget(user_id)

                # Check if adding cost would exceed limit
                if budget.current_spend + cost > budget.limit:
                    raise BudgetExceededException(
                        f"Budget exceeded: ${budget.current_spend:.2f} / ${budget.limit:.2f}",
                        current_spend=budget.current_spend,
                        limit=budget.limit,
                    )

                return True
            except Exception as e:
                await db.rollback()
                raise

    async def track_spend(self, user_id: UUID, cost: float):
        """
        Track spending.

        Args:
            user_id: User ID
            cost: Cost to add
        """
        if not self._enabled:
            return

        # Use a separate session for async task to avoid transaction conflicts
        from app.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            try:
                from app.db.repositories.budget_repo import BudgetRepository
                budget_repo = BudgetRepository(db)
                await budget_repo.update_spend(user_id, cost)
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to track spend: {e}")
                await db.rollback()

    async def check_alerts(self, user_id: UUID):
        """
        Check if budget alert thresholds are crossed.

        Args:
            user_id: User ID
        """
        budget = await self.budget_repo.get_user_budget(user_id)
        if not budget:
            return

        usage_ratio = budget.current_spend / budget.limit if budget.limit > 0 else 0

        for threshold in self._alert_thresholds:
            if usage_ratio >= threshold:
                # Trigger webhook alert (implemented in webhook service)
                logger.warning(f"Budget alert: User {user_id} at {usage_ratio:.1%} of budget")

