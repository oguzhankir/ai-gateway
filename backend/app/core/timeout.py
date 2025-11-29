"""Timeout utilities."""

import asyncio
from typing import TypeVar, Coroutine, Any
from contextlib import asynccontextmanager

from app.core.exceptions import TimeoutException
from app.config import config_manager

T = TypeVar("T")


@asynccontextmanager
async def with_timeout(timeout_seconds: float = None):
    """
    Async context manager for timeout.

    Args:
        timeout_seconds: Timeout in seconds (uses config default if not provided)

    Yields:
        None

    Raises:
        TimeoutException: If timeout occurs
    """
    if timeout_seconds is None:
        timeout_seconds = config_manager.get("timeout.default", 30)

    try:
        yield
    except asyncio.TimeoutError:
        raise TimeoutException(f"Operation timed out after {timeout_seconds} seconds")


async def timeout_wrapper(
    coro: Coroutine[Any, Any, T],
    timeout_seconds: float = None,
) -> T:
    """
    Wrap a coroutine with timeout.

    Args:
        coro: Coroutine to execute
        timeout_seconds: Timeout in seconds (uses config default if not provided)

    Returns:
        Result of coroutine

    Raises:
        TimeoutException: If timeout occurs
    """
    if timeout_seconds is None:
        timeout_seconds = config_manager.get("timeout.default", 30)

    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise TimeoutException(f"Operation timed out after {timeout_seconds} seconds")

