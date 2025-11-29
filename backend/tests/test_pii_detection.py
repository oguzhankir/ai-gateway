"""Tests for PII detection."""

import pytest
from app.pii.detector import pii_detector
from app.pii.entities import PIIType


@pytest.mark.asyncio
async def test_pii_detection_fast_mode():
    """Test fast mode PII detection."""
    text = "My phone number is 555-123-4567 and email is test@example.com"
    result = pii_detector.detect(text, mode="fast")
    
    assert len(result.entities) > 0
    assert result.mode == "fast"
    assert any(e.type == PIIType.PHONE for e in result.entities)
    assert any(e.type == PIIType.EMAIL for e in result.entities)


@pytest.mark.asyncio
async def test_pii_detection_detailed_mode():
    """Test detailed mode PII detection."""
    text = "John Doe works at Acme Corp. Contact: john@example.com"
    result = pii_detector.detect(text, mode="detailed")
    
    assert result.mode == "detailed"
    # Should detect email and potentially person/organization names


@pytest.mark.asyncio
async def test_tckn_validation():
    """Test Turkish ID number validation."""
    from app.pii.patterns import validate_tckn
    
    # Valid TCKN format (example, not a real one)
    assert validate_tckn("12345678901") == False  # Invalid checksum
    
    # Invalid format
    assert validate_tckn("12345") == False
    assert validate_tckn("abc12345678") == False
