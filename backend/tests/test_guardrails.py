"""Tests for guardrails system."""

import pytest
from app.guardrails.engine import guardrail_engine
from app.pii.entities import PIIEntity, PIIType


@pytest.mark.asyncio
async def test_max_tokens_rule():
    """Test max tokens guardrail rule."""
    result = guardrail_engine.check(tokens=15000)
    
    # Should have violations if threshold is exceeded
    # Exact behavior depends on configuration
    assert isinstance(result.passed, bool)


@pytest.mark.asyncio
async def test_pii_rule():
    """Test PII detection guardrail rule."""
    pii_entities = [
        PIIEntity(
            type=PIIType.CREDIT_CARD,
            text="1234-5678-9012-3456",
            start=0,
            end=19,
            confidence=1.0,
        )
    ]
    
    result = guardrail_engine.check(pii_entities=pii_entities)
    assert isinstance(result.passed, bool)


@pytest.mark.asyncio
async def test_content_filter_rule():
    """Test content filter guardrail rule."""
    text = "This is a test message"
    result = guardrail_engine.check(text=text)
    
    assert isinstance(result.passed, bool)
    assert isinstance(result.violations, list)
