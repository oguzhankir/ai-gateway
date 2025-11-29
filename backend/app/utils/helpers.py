"""Helper utility functions."""

from datetime import datetime, timedelta
from typing import Optional


def format_duration_ms(ms: int) -> str:
    """
    Format duration in milliseconds to human-readable string.

    Args:
        ms: Milliseconds

    Returns:
        Formatted string
    """
    if ms < 1000:
        return f"{ms}ms"
    elif ms < 60000:
        return f"{ms / 1000:.2f}s"
    else:
        minutes = ms // 60000
        seconds = (ms % 60000) / 1000
        return f"{minutes}m {seconds:.2f}s"


def format_cost(cost: float) -> str:
    """
    Format cost to currency string.

    Args:
        cost: Cost in USD

    Returns:
        Formatted string
    """
    if cost < 0.01:
        return f"${cost:.4f}"
    elif cost < 1:
        return f"${cost:.3f}"
    else:
        return f"${cost:.2f}"


def format_tokens(tokens: int) -> str:
    """
    Format token count to human-readable string.

    Args:
        tokens: Token count

    Returns:
        Formatted string
    """
    if tokens < 1000:
        return str(tokens)
    elif tokens < 1000000:
        return f"{tokens / 1000:.1f}K"
    else:
        return f"{tokens / 1000000:.2f}M"


def get_period_dates(period: str) -> tuple[datetime, datetime]:
    """
    Get start and end dates for a period.

    Args:
        period: Period string (daily, weekly, monthly)

    Returns:
        Tuple of (start_date, end_date)
    """
    now = datetime.utcnow()
    
    if period == "daily":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    elif period == "weekly":
        days_until_monday = (7 - now.weekday()) % 7
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)
    else:  # monthly
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end = datetime(now.year + 1, 1, 1)
        else:
            end = datetime(now.year, now.month + 1, 1)
    
    return start, end

