"""FastAPI dependencies."""

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.db.session import AsyncSessionLocal
from app.config import settings
from app.core.security import verify_api_key_dependency, verify_admin_key
from app.db.models.user import User


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency.

    Yields:
        Database session
    """
    # Create session without auto-commit
    # Transaction will be managed by the endpoint
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Only commit if no exception occurred
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_redis() -> aioredis.Redis:
    """
    Redis client dependency.

    Returns:
        Redis client
    """
    return await aioredis.from_url(
        settings.redis_url,
        decode_responses=False,
    )


async def get_current_user(
    user: User = Depends(verify_api_key_dependency),
) -> User:
    """
    Get current user from API key.

    Args:
        user: User from API key verification

    Returns:
        User instance
    """
    return user


async def get_admin_user(
    is_admin: bool = Depends(verify_admin_key),
) -> bool:
    """
    Verify admin access.

    Returns:
        True if admin
    """
    return is_admin

