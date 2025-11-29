"""Health check endpoint."""

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.config import settings
import redis.asyncio as aioredis

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "checks": {
            "database": "unknown",
            "redis": "unknown",
            "models": "unknown",
        },
    }

    # Check database
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check Redis
    try:
        redis_client = await aioredis.from_url(settings.redis_url)
        await redis_client.ping()
        await redis_client.aclose()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check spaCy models
    try:
        from app.pii.nlp_models import nlp_models
        nlp_models.get_turkish_model()
        nlp_models.get_english_model()
        health_status["checks"]["models"] = "healthy"
    except Exception as e:
        health_status["checks"]["models"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    return health_status

