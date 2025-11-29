"""Guardrail validators."""

from typing import List, Dict, Any
from app.pii.entities import PIIType, PIIEntity


def validate_content(text: str, patterns: List[str]) -> bool:
    """
    Validate content against regex patterns.

    Args:
        text: Text to validate
        patterns: List of regex patterns

    Returns:
        True if any pattern matches, False otherwise
    """
    import re
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def validate_pii(
    entities: List[PIIEntity],
    entity_types: List[str] = None,
    threshold: int = 1,
) -> bool:
    """
    Validate PII entities.

    Args:
        entities: List of PII entities
        entity_types: List of entity types to check (None = all)
        threshold: Minimum number of entities required

    Returns:
        True if threshold exceeded, False otherwise
    """
    if entity_types:
        filtered = [e for e in entities if e.type.value in entity_types]
        return len(filtered) >= threshold
    return len(entities) >= threshold


def validate_threshold(value: float, threshold: float, comparison: str = "gt") -> bool:
    """
    Validate threshold.

    Args:
        value: Value to check
        threshold: Threshold value
        comparison: Comparison operator (gt, gte, lt, lte, eq)

    Returns:
        True if condition met, False otherwise
    """
    if comparison == "gt":
        return value > threshold
    elif comparison == "gte":
        return value >= threshold
    elif comparison == "lt":
        return value < threshold
    elif comparison == "lte":
        return value <= threshold
    elif comparison == "eq":
        return value == threshold
    return False

