"""Core configuration utilities."""

import os
from typing import Any

from config import get_config, get_config_with_defaults, ConfigError


class AppSettings:
    """Application settings wrapper."""

    def __init__(self) -> None:
        self._config = None

    def _get_config(self):
        """Get configuration, trying file first then defaults."""
        if self._config is None:
            try:
                self._config = get_config()
            except (FileNotFoundError, ConfigError):
                self._config = get_config_with_defaults()
        return self._config

    def _get_env_or_config(self, env_var: str, config_section: str, config_key: str, default: str = "") -> str:
        """Get value from environment variable or config file."""
        # Check environment first
        env_value = os.environ.get(env_var)
        if env_value:
            return env_value
        # Fall back to config
        try:
            return self._get_config().get(config_section, config_key)
        except Exception:
            return default

    @property
    def jwt_secret_key(self) -> str:
        """Get JWT secret key from env or config."""
        return self._get_env_or_config("JWT_SECRET_KEY", "service", "JWT_SECRET_KEY", "default-secret-key")

    @property
    def app_secret_key(self) -> str:
        """Get app secret key from env or config."""
        return self._get_env_or_config("APP_SECRET_KEY", "service", "APP_SECRET_KEY", "default-app-key")

    @property
    def identity(self) -> str:
        """Get service identity from env or config."""
        return self._get_env_or_config("IDENTITY", "service", "IDENTITY", "billing-gpt")

    @property
    def service_shared_secret(self) -> str:
        """Get service shared secret from env or config."""
        return self._get_env_or_config("SRVC_SHARED_SECRET", "service", "SRVC_SHARED_SECRET", "default-secret")

    @property
    def ollama_api_url(self) -> str:
        """Get Ollama API URL from env or config."""
        return self._get_env_or_config("OLLAMA_API_URL", "service", "OLLAMA_API_URL", "http://localhost:11434")

    @property
    def encryption_key(self) -> str:
        """Get encryption key from env or config."""
        return self._get_env_or_config("ENCRYPTION_KEY", "service", "ENCRYPTION_KEY", "encryption.key")

    @property
    def patient_data_encryption_enabled(self) -> bool:
        """Check if patient data encryption is enabled."""
        env_value = os.environ.get("PATIENT_DATA_ENCRYPTION_ENABLED")
        if env_value is not None:
            return env_value.lower() in ("true", "1", "yes")
        try:
            return self._get_config().getboolean("service", "PATIENT_DATA_ENCRYPTION_ENABLED")
        except Exception:
            return True

    @property
    def llms(self) -> list[str]:
        """Get list of LLM models from env or config."""
        env_value = os.environ.get("LLMS")
        if env_value:
            return env_value.split(",")
        try:
            return self._get_config().get("service", "LLMS").split(",")
        except Exception:
            return ["llama3.2"]

    @property
    def medllms(self) -> list[str]:
        """Get list of medical LLM models from env or config."""
        env_value = os.environ.get("MEDLLMS")
        if env_value:
            return env_value.split(",")
        try:
            return self._get_config().get("service", "MEDLLMS").split(",")
        except Exception:
            return ["medllama2"]

    @property
    def endpoint_url(self) -> str:
        """Get endpoint URL from env or config."""
        return self._get_env_or_config("ENDPOINT_URL", "service", "ENDPOINT_URL", "http://localhost:5000")


# Global settings instance
settings = AppSettings()
