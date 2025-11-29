"""Custom guardrail loader."""

from pathlib import Path
from typing import List, Dict, Any
import yaml

from app.guardrails.rules import (
    BaseRule,
    MaxTokensRule,
    NoPIIRule,
    ContentFilterRule,
    MaxCostRule,
)


class CustomRuleLoader:
    """Loader for custom guardrail rules from YAML."""

    def __init__(self):
        self.config_path = Path(__file__).parent.parent.parent / "config" / "guardrails.yaml"

    def load_rules(self) -> List[BaseRule]:
        """
        Load custom rules from YAML.

        Returns:
            List of rule instances
        """
        if not self.config_path.exists():
            return []

        with open(self.config_path, "r") as f:
            config = yaml.safe_load(f) or {}

        rules_config = config.get("rules", [])
        rules = []

        for rule_config in rules_config:
            rule = self._create_rule(rule_config)
            if rule:
                rules.append(rule)

        return rules

    def _create_rule(self, config: Dict[str, Any]) -> BaseRule:
        """
        Create rule instance from config.

        Args:
            config: Rule configuration dictionary

        Returns:
            Rule instance
        """
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
            if "cost" in name.lower() or "cost" in config.get("description", "").lower():
                return MaxCostRule(threshold=threshold, **base_kwargs)
            else:
                return MaxTokensRule(threshold=threshold, **base_kwargs)

        elif rule_type == "pii":
            entity_types = config.get("entity_types", [])
            return NoPIIRule(entity_types=entity_types, **base_kwargs)

        elif rule_type == "content":
            patterns = config.get("patterns", [])
            return ContentFilterRule(patterns=patterns, **base_kwargs)

        return None


# Singleton instance
custom_rule_loader = CustomRuleLoader()

