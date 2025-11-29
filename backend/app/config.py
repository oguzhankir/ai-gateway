"""Configuration management for the AI Gateway application."""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ai_gateway",
        env="DATABASE_URL"
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )

    # API Keys
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    gemini_api_key: str = Field(default="", env="GEMINI_API_KEY")

    # Security
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    admin_api_key: str = Field(
        default="dev-admin-key-change-in-production",
        env="ADMIN_API_KEY"
    )

    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


class ConfigManager:
    """Singleton configuration manager for YAML-based configuration."""

    _instance: Optional["ConfigManager"] = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._config:
            self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML files."""
        config_dir = Path(__file__).parent.parent / "config"
        environment = os.getenv("ENVIRONMENT", "development")

        # Load base configuration
        base_config_path = config_dir / "config.yaml"
        if base_config_path.exists():
            with open(base_config_path, "r") as f:
                self._config = yaml.safe_load(f) or {}

        # Load environment-specific overrides
        env_config_path = config_dir / f"config.{environment}.yaml"
        if env_config_path.exists():
            with open(env_config_path, "r") as f:
                env_config = yaml.safe_load(f) or {}
                self._config = self._deep_merge(self._config, env_config)

        # Substitute environment variables in string values
        self._substitute_env_vars(self._config)

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _substitute_env_vars(self, config: Dict[str, Any]) -> None:
        """Recursively substitute environment variables in string values."""
        for key, value in config.items():
            if isinstance(value, dict):
                self._substitute_env_vars(value)
            elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                config[key] = os.getenv(env_var, value)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key: Configuration key in dot notation (e.g., "server.port")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration."""
        return self._config.copy()


# Singleton instances
config_manager = ConfigManager()
settings = Settings()

