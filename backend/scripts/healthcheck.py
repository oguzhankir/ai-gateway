"""Health check script for Docker."""

import sys
from pathlib import Path
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import AsyncSessionLocal
from app.config import settings
import redis.asyncio as aioredis


async def check_database():
    """Check database connection."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def check_redis():
    """Check Redis connection."""
    try:
        redis_client = await aioredis.from_url(settings.redis_url)
        await redis_client.ping()
        await redis_client.aclose()
        return True
    except Exception:
        return False


async def main():
    """Run health checks."""
    db_ok = await check_database()
    redis_ok = await check_redis()

    if db_ok and redis_ok:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

