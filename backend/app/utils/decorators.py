"""Custom decorators."""

import asyncio
import time
from functools import wraps
from typing import Callable, Any


def async_retry(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Async retry decorator.

    Args:
        max_retries: Maximum number of retries
        delay: Initial delay in seconds
        backoff: Backoff multiplier
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise last_exception

            raise last_exception

        return wrapper
    return decorator


def timing(func: Callable) -> Callable:
    """
    Timing decorator to measure function execution time.

    Args:
        func: Function to time

    Returns:
        Wrapped function
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = (time.time() - start) * 1000  # Convert to ms
            print(f"{func.__name__} took {duration:.2f}ms")

    @wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        start = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = (time.time() - start) * 1000
            print(f"{func.__name__} took {duration:.2f}ms")

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

