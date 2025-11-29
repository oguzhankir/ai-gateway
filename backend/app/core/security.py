"""Security utilities for API key management."""

import secrets
import bcrypt
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings
from app.db.models.api_key import APIKey
from app.db.models.user import User
from app.core.exceptions import AuthenticationException


api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using bcrypt.

    Args:
        api_key: The API key to hash

    Returns:
        Hashed API key
    """
    return bcrypt.hashpw(api_key.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_api_key(api_key: str, hashed: str) -> bool:
    """
    Verify an API key against its hash.

    Args:
        api_key: The API key to verify
        hashed: The hashed API key

    Returns:
        True if the API key matches, False otherwise
    """
    try:
        return bcrypt.checkpw(api_key.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def generate_api_key() -> str:
    """
    Generate a new API key.

    Returns:
        A new API key string
    """
    return f"sk-{secrets.token_urlsafe(32)}"


async def verify_api_key_dependency(
    authorization: Optional[str] = Security(api_key_header),
) -> User:
    """
    FastAPI dependency to verify API key and return user.

    Args:
        authorization: Authorization header value

    Returns:
        User object

    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )

    # Handle Bearer token format
    if authorization.startswith("Bearer "):
        api_key = authorization[7:]
    else:
        api_key = authorization

    # Check admin key first
    if api_key == settings.admin_api_key:
        # Return admin user from database using separate session
        from sqlalchemy import select
        from app.db.session import AsyncSessionLocal
        
        # Create a new session - it will be closed automatically
        # Don't use begin() to avoid nested transaction issues
        async with AsyncSessionLocal() as db_session:
            # Execute query - session will auto-commit on close if no exception
            result = await db_session.execute(select(User).where(User.username == "admin"))
            admin_user = result.scalar_one_or_none()
            if admin_user:
                # Create a detached copy
                detached_user = User(
                    id=admin_user.id,
                    username=admin_user.username,
                    email=admin_user.email,
                    created_at=admin_user.created_at
                )
                # Rollback to avoid committing (read-only operation)
                await db_session.rollback()
                return detached_user
            else:
                await db_session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Admin user not found in database",
                )

    # Find API key in database using separate session
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.db.session import AsyncSessionLocal

    # Create a new session - it will be closed automatically
    # Don't use begin() to avoid nested transaction issues
    async with AsyncSessionLocal() as db_session:
        stmt = select(APIKey).options(selectinload(APIKey.user)).where(APIKey.is_active == True)
        result = await db_session.execute(stmt)
        api_keys = result.scalars().all()

        for key in api_keys:
            if verify_api_key(api_key, key.key_hash):
                # Get user and create a detached copy
                user = key.user
                # Create a new User object with same data but detached from session
                detached_user = User(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    created_at=user.created_at
                )
                # Rollback to avoid committing (read-only operation)
                await db_session.rollback()
                return detached_user
        
        await db_session.rollback()

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
    )


async def verify_admin_key(
    authorization: Optional[str] = Security(api_key_header),
) -> bool:
    """
    FastAPI dependency to verify admin API key.

    Args:
        authorization: Authorization header value

    Returns:
        True if admin key is valid

    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )

    if authorization.startswith("Bearer "):
        api_key = authorization[7:]
    else:
        api_key = authorization

    if api_key == settings.admin_api_key:
        return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin access required",
    )

