"""Tests for services/logging_service.py — structured logging."""
import json
import logging
import os
from unittest.mock import patch

import pytest
from services.logging_service import (
    setup_logging,
    log_scan_event,
    log_api_call,
    log_issue_detected,
    log_review_action,
)


class TestSetupLogging:
    """Tests for logging initialization."""

    def test_local_dev_setup(self, caplog):
        """Development mode uses standard Python logging."""
        with patch.dict(os.environ, {"ENV": "development"}, clear=False):
            setup_logging()
            # Should not raise

    def test_production_without_cloud_logging(self, caplog):
        """Production mode falls back gracefully if Cloud Logging unavailable."""
        with patch.dict(os.environ, {"ENV": "production"}, clear=False):
            # Cloud Logging import will fail in test env — should fall back
            setup_logging()


class TestLogScanEvent:
    """Tests for log_scan_event."""

    def test_event_structure(self, caplog):
        """Log event contains required fields."""
        with caplog.at_level(logging.INFO, logger="docugardener"):
            log_scan_event("scan_started", {"doc_id": "test_doc"})

        assert len(caplog.records) == 1
        event = json.loads(caplog.records[0].message)
        assert event["event_type"] == "scan_started"
        assert "timestamp" in event
        assert event["component"] == "docugardener"
        assert event["metadata"]["doc_id"] == "test_doc"

    def test_event_without_metadata(self, caplog):
        """Log event works without metadata."""
        with caplog.at_level(logging.INFO, logger="docugardener"):
            log_scan_event("scan_completed")

        event = json.loads(caplog.records[0].message)
        assert event["event_type"] == "scan_completed"
        assert "metadata" not in event


class TestLogApiCall:
    """Tests for log_api_call."""

    def test_successful_call(self, caplog):
        """Successful API call is logged at INFO level."""
        with caplog.at_level(logging.INFO, logger="docugardener"):
            log_api_call("gemini", "compare_text", 1234.5, True)

        event = json.loads(caplog.records[0].message)
        assert event["service"] == "gemini"
        assert event["method"] == "compare_text"
        assert event["duration_ms"] == 1234.5
        assert event["success"] is True
        assert caplog.records[0].levelno == logging.INFO

    def test_failed_call(self, caplog):
        """Failed API call is logged at ERROR level with error message."""
        with caplog.at_level(logging.ERROR, logger="docugardener"):
            log_api_call("firestore", "save", 500.0, False, "timeout")

        event = json.loads(caplog.records[0].message)
        assert event["success"] is False
        assert event["error"] == "timeout"
        assert caplog.records[0].levelno == logging.ERROR

    def test_error_truncation(self, caplog):
        """Long error messages are truncated to 500 chars."""
        long_error = "x" * 1000
        with caplog.at_level(logging.ERROR, logger="docugardener"):
            log_api_call("drive", "list", 100.0, False, long_error)

        event = json.loads(caplog.records[0].message)
        assert len(event["error"]) == 500


class TestLogIssueDetected:
    """Tests for log_issue_detected."""

    def test_issue_event(self, caplog):
        """Issue detection is logged with correct metadata."""
        with caplog.at_level(logging.INFO, logger="docugardener"):
            log_issue_detected("scan_001", "contradiction", "critical", "ナビゲーション")

        event = json.loads(caplog.records[0].message)
        assert event["event_type"] == "issue_detected"
        assert event["metadata"]["scan_id"] == "scan_001"
        assert event["metadata"]["severity"] == "critical"


class TestLogReviewAction:
    """Tests for log_review_action."""

    def test_approval_event(self, caplog):
        """Review approval is logged correctly."""
        with caplog.at_level(logging.INFO, logger="docugardener"):
            log_review_action("scan_001", "c_0", "approved", "admin")

        event = json.loads(caplog.records[0].message)
        assert event["event_type"] == "review_action"
        assert event["metadata"]["action"] == "approved"
        assert event["metadata"]["reviewer"] == "admin"
