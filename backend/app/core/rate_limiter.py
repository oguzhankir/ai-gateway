"""Rate limiting using Redis sliding window."""

import time
from typing import Optional, Tuple
import redis.asyncio as aioredis

from app.config import config_manager, settings
from app.core.exceptions import RateLimitException


class RateLimiter:
    """Redis-based rate limiter using sliding window."""

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self._enabled = config_manager.get("rate_limiting.enabled", True)
        self._tiers = config_manager.get("rate_limiting.tiers", {})

    async def initialize(self):
        """Initialize Redis connection."""
        if self._enabled:
            self.redis = await aioredis.from_url(
                settings.redis_url,
                decode_responses=False,
            )

    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.aclose()

    async def check_rate_limit(
        self,
        user_id: str,
        tier: str = "default",
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if user has exceeded rate limit.

        Args:
            user_id: User ID
            tier: Rate limit tier (default, premium, etc.)

        Returns:
            Tuple of (allowed, retry_after_seconds)

        Raises:
            RateLimitException: If rate limit exceeded
        """
        if not self._enabled:
            return True, None

        if not self.redis:
            await self.initialize()

        tier_config = self._tiers.get(tier, self._tiers.get("default", {}))
        per_minute = tier_config.get("requests_per_minute", 60)
        per_hour = tier_config.get("requests_per_hour", 1000)

        now = time.time()
        minute_window = 60
        hour_window = 3600

        # Check per-minute limit
        minute_key = f"rate_limit:{user_id}:minute"
        minute_count = await self.redis.zcount(
            minute_key,
            now - minute_window,
            now,
        )

        if minute_count >= per_minute:
            retry_after = int(minute_window - (now % minute_window)) + 1
            raise RateLimitException(
                f"Rate limit exceeded: {per_minute} requests per minute",
                retry_after=retry_after,
            )

        # Check per-hour limit
        hour_key = f"rate_limit:{user_id}:hour"
        hour_count = await self.redis.zcount(
            hour_key,
            now - hour_window,
            now,
        )

        if hour_count >= per_hour:
            retry_after = int(hour_window - (now % hour_window)) + 1
            raise RateLimitException(
                f"Rate limit exceeded: {per_hour} requests per hour",
                retry_after=retry_after,
            )

        # Record request
        await self.redis.zadd(minute_key, {str(now): now})
        await self.redis.zadd(hour_key, {str(now): now})
        await self.redis.expire(minute_key, minute_window)
        await self.redis.expire(hour_key, hour_window)

        # Clean old entries
        await self.redis.zremrangebyscore(minute_key, 0, now - minute_window)
        await self.redis.zremrangebyscore(hour_key, 0, now - hour_window)

        return True, None


# Singleton instance
rate_limiter = RateLimiter()

