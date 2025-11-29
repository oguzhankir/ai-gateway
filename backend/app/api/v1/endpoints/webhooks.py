"""Webhook endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import secrets

from app.dependencies import get_db, get_current_user
from app.db.models.user import User
from app.schemas.webhook import WebhookCreate, WebhookResponse
from app.services.webhook_service import WebhookService
from app.db.repositories.webhook_repo import WebhookRepository

router = APIRouter()


@router.post("", response_model=WebhookResponse)
async def create_webhook(
    webhook: WebhookCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a webhook."""
    repo = WebhookRepository(db)
    
    # Generate secret if not provided
    secret = webhook.secret or f"secret_{secrets.token_urlsafe(32)}"
    
    webhook_data = {
        "user_id": user.id,
        "url": webhook.url,
        "events": webhook.events,
        "secret": secret,
        "is_active": True,
    }
    
    created = await repo.create(webhook_data)
    await db.commit()
    
    return WebhookResponse(
        id=created.id,
        url=created.url,
        events=created.events,
        is_active=created.is_active,
        created_at=created.created_at,
        updated_at=created.updated_at,
    )


@router.get("", response_model=list[WebhookResponse])
async def list_webhooks(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List user's webhooks."""
    repo = WebhookRepository(db)
    webhooks = await repo.get_by_user(user.id)
    
    return [
        WebhookResponse(
            id=w.id,
            url=w.url,
            events=w.events,
            is_active=w.is_active,
            created_at=w.created_at,
            updated_at=w.updated_at,
        )
        for w in webhooks
    ]


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a webhook."""
    repo = WebhookRepository(db)
    webhook = await repo.get_by_id(webhook_id)
    
    if not webhook or webhook.user_id != user.id:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    await repo.delete(webhook_id)
    await db.commit()
    
    return {"success": True}

