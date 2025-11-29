"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.endpoints import gateway, streaming, analytics, webhooks, guardrails, health

router = APIRouter()

router.include_router(gateway.router, tags=["gateway"])
router.include_router(streaming.router, tags=["streaming"])
router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
router.include_router(guardrails.router, prefix="/guardrails", tags=["guardrails"])
router.include_router(health.router, tags=["health"])

