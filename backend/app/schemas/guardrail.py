"""Guardrail schemas."""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class Violation(BaseModel):
    """Guardrail violation."""

    rule_name: str
    severity: str
    message: str
    details: Optional[Dict[str, Any]] = None


class GuardrailResult(BaseModel):
    """Guardrail check result."""

    passed: bool
    violations: List[Violation]
    should_block: bool

