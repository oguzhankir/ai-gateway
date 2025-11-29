"""Guardrail engine."""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from app.config import config_manager
from app.pii.entities import PIIEntity
from app.guardrails.rules import BaseRule, GuardrailViolation, MaxTokensRule, NoPIIRule, ContentFilterRule
from app.guardrails.custom import custom_rule_loader


@dataclass
class GuardrailResult:
    """Guardrail check result."""

    passed: bool
    violations: List[GuardrailViolation]
    should_block: bool


class GuardrailEngine:
    """Engine for running guardrail checks."""

    def __init__(self):
        self._enabled = config_manager.get("guardrails.enabled", True)
        self._block_on_violation = config_manager.get("guardrails.block_on_violation", True)
        self._rules: List[BaseRule] = []
        self._load_rules()

    def _load_rules(self):
        """Load built-in and custom rules."""
        # Load built-in rules from config
        builtin_rules_config = config_manager.get("guardrails.rules", [])

        for rule_config in builtin_rules_config:
            rule = self._create_builtin_rule(rule_config)
            if rule:
                self._rules.append(rule)

        # Load custom rules
        custom_rules = custom_rule_loader.load_rules()
        self._rules.extend(custom_rules)

    def _create_builtin_rule(self, config: Dict[str, Any]) -> Optional[BaseRule]:
        """Create built-in rule from config."""
        rule_type = config.get("type", "")
        name = config.get("name", "")
        enabled = config.get("enabled", True)
        severity = config.get("severity", "warning")
        action = config.get("action", "log")

        base_kwargs = {
            "name": name,
            "rule_type": rule_type,
            "enabled": enabled,
            "severity": severity,
            "action": action,
        }

        if rule_type == "threshold":
            threshold = config.get("threshold", 0)
            if "token" in name.lower():
                return MaxTokensRule(threshold=threshold, **base_kwargs)
            else:
                # Default to token rule
                return MaxTokensRule(threshold=threshold, **base_kwargs)

        elif rule_type == "pii":
            entity_types = config.get("entity_types", [])
            return NoPIIRule(entity_types=entity_types, **base_kwargs)

        elif rule_type == "content":
            patterns = config.get("patterns", [])
            return ContentFilterRule(patterns=patterns, **base_kwargs)

        return None

    def check(
        self,
        text: Optional[str] = None,
        pii_entities: Optional[List[PIIEntity]] = None,
        tokens: Optional[int] = None,
        cost: Optional[float] = None,
        **kwargs,
    ) -> GuardrailResult:
        """
        Run guardrail checks.

        Args:
            text: Text to check
            pii_entities: Detected PII entities
            tokens: Token count
            cost: Cost in USD
            **kwargs: Additional context

        Returns:
            GuardrailResult
        """
        if not self._enabled:
            return GuardrailResult(passed=True, violations=[], should_block=False)

        violations = []
        should_block = False

        for rule in self._rules:
            if not rule.enabled:
                continue

            violation = rule.check(
                text=text,
                pii_entities=pii_entities,
                tokens=tokens,
                cost=cost,
                **kwargs,
            )

            if violation:
                violations.append(violation)
                if violation.severity == "error" and self._block_on_violation:
                    should_block = True

        passed = len(violations) == 0
        return GuardrailResult(
            passed=passed,
            violations=violations,
            should_block=should_block,
        )


# Singleton instance
guardrail_engine = GuardrailEngine()

