"""Cloud Logging integration for DocuAlign AI.

Provides structured logging for production environments using Google Cloud Logging,
with automatic fallback to standard Python logging for local development.
"""
import os
import logging
import json
from datetime import datetime, timezone


logger = logging.getLogger("docugardener")


def setup_logging():
    """Initialize logging based on environment.
    
    - Production (ENV=production): Uses Google Cloud Logging
    - Development: Uses standard Python logging with colored output
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    if os.getenv("ENV") == "production":
        try:
            from google.cloud import logging as cloud_logging
            
            client = cloud_logging.Client()
            client.setup_logging(log_level=getattr(logging, log_level))
            logger.info("✅ Cloud Logging initialized (production mode)")
        except Exception as e:
            _setup_local_logging(log_level)
            logger.warning(f"Cloud Logging init failed, using local: {e}")
    else:
        _setup_local_logging(log_level)
        logger.info("📝 Local logging initialized (development mode)")


def _setup_local_logging(log_level: str):
    """Configure colored local logging."""
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def log_scan_event(event_type: str, metadata: dict | None = None):
    """Log a structured scan event.
    
    Args:
        event_type: Type of event (scan_started, scan_completed, gemini_api_call, etc.)
        metadata: Additional metadata dict
    """
    event = {
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "docugardener",
        "environment": os.getenv("ENV", "development"),
    }
    if metadata:
        event["metadata"] = metadata
    
    logger.info(json.dumps(event, ensure_ascii=False, default=str))


def log_api_call(service: str, method: str, duration_ms: float, success: bool, error: str | None = None):
    """Log an API call with timing information.
    
    Args:
        service: Service name (gemini, firestore, drive, etc.)
        method: Method called
        duration_ms: Call duration in milliseconds
        success: Whether the call succeeded
        error: Error message if failed
    """
    event = {
        "event_type": "api_call",
        "service": service,
        "method": method,
        "duration_ms": round(duration_ms, 2),
        "success": success,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if error:
        event["error"] = str(error)[:500]
    
    if success:
        logger.info(json.dumps(event, ensure_ascii=False, default=str))
    else:
        logger.error(json.dumps(event, ensure_ascii=False, default=str))


def log_issue_detected(scan_id: str, issue_type: str, severity: str, category: str):
    """Log when an issue is detected.
    
    Args:
        scan_id: Scan identifier
        issue_type: contradiction or visual_decay
        severity: critical, warning, info
        category: Issue category
    """
    log_scan_event("issue_detected", {
        "scan_id": scan_id,
        "issue_type": issue_type,
        "severity": severity,
        "category": category,
    })


def log_review_action(scan_id: str, issue_key: str, action: str, reviewer: str = "admin"):
    """Log when an issue is reviewed (approved/denied).
    
    Args:
        scan_id: Scan identifier
        issue_key: Issue key
        action: approved or denied
        reviewer: Who reviewed
    """
    log_scan_event("review_action", {
        "scan_id": scan_id,
        "issue_key": issue_key,
        "action": action,
        "reviewer": reviewer,
    })
