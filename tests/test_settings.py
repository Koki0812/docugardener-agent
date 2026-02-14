"""Tests for config/settings.py — secret management and configuration."""
import os
from unittest.mock import patch

import pytest
from config.settings import get_secret


class TestGetSecret:
    """Tests for get_secret function."""

    def test_local_dev_uses_env_var(self):
        """In non-production, returns environment variable."""
        with patch.dict(os.environ, {"ENV": "development", "MY_SECRET": "dev_value"}):
            result = get_secret("my-secret")
            assert result == "dev_value"

    def test_hyphen_to_underscore(self):
        """Secret IDs with hyphens are converted to uppercase underscore env vars."""
        with patch.dict(os.environ, {"ENV": "development", "SEARCH_ENGINE_ID": "abc123"}):
            result = get_secret("search-engine-id")
            assert result == "abc123"

    def test_default_value(self):
        """Returns default when env var not set."""
        with patch.dict(os.environ, {"ENV": "development"}, clear=True):
            result = get_secret("nonexistent", "fallback")
            assert result == "fallback"

    def test_empty_default(self):
        """Default value is empty string when not specified."""
        with patch.dict(os.environ, {"ENV": "development"}, clear=True):
            result = get_secret("nonexistent")
            assert result == ""

    def test_production_fallback_on_error(self):
        """Production mode falls back to env var if Secret Manager fails."""
        with patch.dict(os.environ, {
            "ENV": "production",
            "GCP_PROJECT_ID": "test-project",
            "MY_KEY": "env_fallback",
        }):
            # Secret Manager will fail (not available in test env)
            result = get_secret("my-key", "default")
            # Should fall back to env var or default
            assert result in ("env_fallback", "default")

    def test_production_no_project_id(self):
        """Production without GCP_PROJECT_ID falls back to env var."""
        env = {"ENV": "production", "MY_VAR": "from_env"}
        with patch.dict(os.environ, env, clear=True):
            result = get_secret("my-var")
            assert result == "from_env"
