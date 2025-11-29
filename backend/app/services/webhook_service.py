"""Webhook service for event notifications."""

import hmac
import hashlib
import json
import asyncio
from typing import List, Dict, Any
from uuid import UUID
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.webhook_repo import WebhookRepository
from app.config import config_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WebhookService:
    """Service for webhook notifications."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.webhook_repo = WebhookRepository(db)
        self._enabled = config_manager.get("webhooks.enabled", True)
        self._timeout = config_manager.get("webhooks.timeout", 5)
        self._max_retries = config_manager.get("webhooks.max_retries", 3)
        self._retry_delay = config_manager.get("webhooks.retry_delay", 1.0)

    async def trigger_event(self, event_type: str, data: Dict[str, Any]):
        """
        Trigger webhook event.

        Args:
            event_type: Event type
            data: Event data
        """
        if not self._enabled:
            return

        # Use a separate session to avoid transaction conflicts
        from app.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            try:
                webhook_repo = WebhookRepository(db)
                webhooks = await webhook_repo.get_active_webhooks(event_type)
                
                for webhook in webhooks:
                    asyncio.create_task(self._deliver_webhook(webhook, event_type, data))
            except Exception as e:
                logger.error(f"Failed to get webhooks: {e}")
                # Don't raise - webhooks are not critical

    async def _deliver_webhook(
        self,
        webhook,
        event_type: str,
        data: Dict[str, Any],
    ):
        """
        Deliver webhook with retry logic.

        Args:
            webhook: Webhook instance
            event_type: Event type
            data: Event data
        """
        payload = {
            "event": event_type,
            "timestamp": data.get("timestamp"),
            "data": data,
        }

        signature = self._generate_signature(webhook.secret, json.dumps(payload))

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": event_type,
        }

        for attempt in range(self._max_retries):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(
                        webhook.url,
                        json=payload,
                        headers=headers,
                    )
                    response.raise_for_status()
                    logger.info(f"Webhook delivered: {webhook.url} (event: {event_type})")
                    return
            except Exception as e:
                logger.warning(f"Webhook delivery failed (attempt {attempt + 1}/{self._max_retries}): {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (2 ** attempt))

        logger.error(f"Webhook delivery failed after {self._max_retries} attempts: {webhook.url}")

    def _generate_signature(self, secret: str, payload: str) -> str:
        """
        Generate HMAC signature.

        Args:
            secret: Secret key
            payload: Payload string

        Returns:
            Signature string
        """
        return hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

