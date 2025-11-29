"""Built-in guardrail rules."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.pii.entities import PIIEntity
from app.guardrails.validators import validate_content, validate_pii, validate_threshold


@dataclass
class GuardrailViolation:
    """Guardrail violation."""

    rule_name: str
    severity: str
    message: str
    details: Optional[Dict[str, Any]] = None


class BaseRule:
    """Base guardrail rule."""

    def __init__(
        self,
        name: str,
        rule_type: str,
        enabled: bool = True,
        severity: str = "warning",
        action: str = "log",
    ):
        self.name = name
        self.rule_type = rule_type
        self.enabled = enabled
        self.severity = severity
        self.action = action

    def check(
        self,
        text: Optional[str] = None,
        pii_entities: Optional[List[PIIEntity]] = None,
        tokens: Optional[int] = None,
        cost: Optional[float] = None,
        **kwargs,
    ) -> Optional[GuardrailViolation]:
        """
        Check rule.

        Args:
            text: Text to check
            pii_entities: Detected PII entities
            tokens: Token count
            cost: Cost in USD
            **kwargs: Additional context

        Returns:
            GuardrailViolation if violated, None otherwise
        """
        raise NotImplementedError


class MaxTokensRule(BaseRule):
    """Rule for maximum tokens."""

    def __init__(self, threshold: int, **kwargs):
        super().__init__(**kwargs)
        self.threshold = threshold

    def check(self, tokens: Optional[int] = None, **kwargs) -> Optional[GuardrailViolation]:
        """Check token threshold."""
        if not self.enabled or tokens is None:
            return None

        if tokens > self.threshold:
            return GuardrailViolation(
                rule_name=self.name,
                severity=self.severity,
                message=f"Token count {tokens} exceeds threshold {self.threshold}",
                details={"tokens": tokens, "threshold": self.threshold},
            )
        return None


class NoPIIRule(BaseRule):
    """Rule for blocking PII in output."""

    def __init__(self, entity_types: List[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.entity_types = entity_types or []

    def check(
        self,
        text: Optional[str] = None,
        pii_entities: Optional[List[PIIEntity]] = None,
        **kwargs,
    ) -> Optional[GuardrailViolation]:
        """Check for PII."""
        if not self.enabled:
            return None

        if pii_entities:
            filtered = [
                e for e in pii_entities
                if not self.entity_types or e.type.value in self.entity_types
            ]
            if filtered:
                return GuardrailViolation(
                    rule_name=self.name,
                    severity=self.severity,
                    message=f"PII detected: {[e.type.value for e in filtered]}",
                    details={"entities": [e.to_dict() for e in filtered]},
                )
        return None


class ContentFilterRule(BaseRule):
    """Rule for content filtering."""

    def __init__(self, patterns: List[str], **kwargs):
        super().__init__(**kwargs)
        self.patterns = patterns

    def check(self, text: Optional[str] = None, **kwargs) -> Optional[GuardrailViolation]:
        """Check content patterns."""
        if not self.enabled or not text:
            return None

        if validate_content(text, self.patterns):
            return GuardrailViolation(
                rule_name=self.name,
                severity=self.severity,
                message="Content matches filtered patterns",
                details={"patterns": self.patterns},
            )
        return None


class MaxCostRule(BaseRule):
    """Rule for maximum cost per request."""

    def __init__(self, threshold: float, **kwargs):
        super().__init__(**kwargs)
        self.threshold = threshold

    def check(self, cost: Optional[float] = None, **kwargs) -> Optional[GuardrailViolation]:
        """Check cost threshold."""
        if not self.enabled or cost is None:
            return None

        if cost > self.threshold:
            return GuardrailViolation(
                rule_name=self.name,
                severity=self.severity,
                message=f"Cost ${cost:.4f} exceeds threshold ${self.threshold:.4f}",
                details={"cost": cost, "threshold": self.threshold},
            )
        return None

