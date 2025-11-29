"""Guardrail endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.db.models.user import User
from app.schemas.guardrail import GuardrailResult
from app.guardrails.engine import guardrail_engine
from app.db.repositories.guardrail_repo import GuardrailRepository

router = APIRouter()


@router.get("", response_model=list[dict])
async def list_guardrails(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List guardrail rules."""
    rules = []
    for rule in guardrail_engine._rules:
        rules.append({
            "name": rule.name,
            "type": rule.rule_type,
            "enabled": rule.enabled,
            "severity": rule.severity,
            "action": rule.action,
        })
    return rules


@router.get("/violations", response_model=list[dict])
async def get_violations(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = 100,
):
    """Get recent guardrail violations."""
    guardrail_repo = GuardrailRepository(db)
    violations = await guardrail_repo.get_recent(user_id=user.id, limit=limit)
    
    return [
        {
            "id": str(v.id),
            "user_id": str(v.user_id),
            "request_id": str(v.request_id) if v.request_id else None,
            "rule_name": v.rule_name,
            "severity": v.severity,
            "action": v.action,
            "details": v.details,
            "timestamp": v.timestamp.isoformat(),
        }
        for v in violations
    ]

