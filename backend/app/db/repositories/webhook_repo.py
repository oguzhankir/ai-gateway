"""Webhook repository for webhook operations."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.webhook import Webhook


class WebhookRepository:
    """Repository for webhook operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, webhook_data: dict) -> Webhook:
        """
        Create a new webhook.

        Args:
            webhook_data: Webhook data dictionary

        Returns:
            Created Webhook instance
        """
        webhook = Webhook(**webhook_data)
        self.db.add(webhook)
        await self.db.flush()
        return webhook

    async def get_by_id(self, webhook_id: UUID) -> Optional[Webhook]:
        """
        Get webhook by ID.

        Args:
            webhook_id: Webhook ID

        Returns:
            Webhook instance or None
        """
        result = await self.db.execute(
            select(Webhook).where(Webhook.id == webhook_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: UUID) -> List[Webhook]:
        """
        Get all webhooks for a user.

        Args:
            user_id: User ID

        Returns:
            List of Webhook instances
        """
        result = await self.db.execute(
            select(Webhook).where(Webhook.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_active_webhooks(self, event_type: str) -> List[Webhook]:
        """
        Get active webhooks for an event type.

        Args:
            event_type: Event type to filter by

        Returns:
            List of active Webhook instances
        """
        result = await self.db.execute(
            select(Webhook).where(
                and_(
                    Webhook.is_active == True,
                    Webhook.events.contains([event_type]),
                )
            )
        )
        return list(result.scalars().all())

    async def update(self, webhook_id: UUID, update_data: dict) -> Optional[Webhook]:
        """
        Update a webhook.

        Args:
            webhook_id: Webhook ID
            update_data: Update data dictionary

        Returns:
            Updated Webhook instance or None
        """
        webhook = await self.get_by_id(webhook_id)
        if not webhook:
            return None

        for key, value in update_data.items():
            setattr(webhook, key, value)

        await self.db.flush()
        return webhook

    async def delete(self, webhook_id: UUID) -> bool:
        """
        Delete a webhook.

        Args:
            webhook_id: Webhook ID

        Returns:
            True if deleted, False if not found
        """
        webhook = await self.get_by_id(webhook_id)
        if not webhook:
            return False

        await self.db.delete(webhook)
        await self.db.flush()
        return True

