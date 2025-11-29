"""PII entity definitions."""

from enum import Enum
from typing import List, Optional
from dataclasses import dataclass


class PIIType(str, Enum):
    """PII entity types."""

    TCKN = "TCKN"  # Turkish ID number
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    IBAN = "IBAN"
    CREDIT_CARD = "CREDIT_CARD"
    ADDRESS = "ADDRESS"
    AMOUNT = "AMOUNT"
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    DATE = "DATE"


@dataclass
class PIIEntity:
    """PII entity detected in text."""

    type: PIIType
    text: str
    start: int
    end: int
    confidence: float = 1.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "text": self.text,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
        }


@dataclass
class PIIDetectionResult:
    """Result of PII detection."""

    entities: List[PIIEntity]
    mode: str  # "fast" or "detailed"
    processing_time_ms: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "entities": [entity.to_dict() for entity in self.entities],
            "mode": self.mode,
            "processing_time_ms": self.processing_time_ms,
            "count": len(self.entities),
        }

