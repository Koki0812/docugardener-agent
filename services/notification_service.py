"""
Notification service for DocuAlign AI.

Sends real-time alerts via Google Cloud Pub/Sub when:
- New contradictions are detected
- Critical issues require immediate attention
- Scan jobs complete
- Review deadlines approach

Consumers can subscribe to topics and route to:
- Email (via Cloud Functions + SendGrid)
- Slack (via webhook)
- In-app notifications (stored in Firestore)
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger("docualign.notifications")

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
TOPIC_SCAN_COMPLETE = os.environ.get("PUBSUB_TOPIC_SCAN", "docualign-scan-complete")
TOPIC_CRITICAL_ALERT = os.environ.get("PUBSUB_TOPIC_ALERT", "docualign-critical-alert")

NOTIFICATIONS_COLLECTION = "notifications"


def _get_pubsub_client():
    """Lazily initialize Pub/Sub publisher client."""
    try:
        from google.cloud import pubsub_v1
        return pubsub_v1.PublisherClient()
    except Exception as e:
        logger.warning(f"Pub/Sub client init failed: {e}")
        return None


def _get_firestore_client():
    """Lazily initialize Firestore client for in-app notifications."""
    try:
        from google.cloud import firestore
        project = os.environ.get("GCP_PROJECT_ID", "")
        return firestore.Client(project=project) if project else firestore.Client()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Pub/Sub Publishing
# ---------------------------------------------------------------------------

def publish_event(
    topic_name: str,
    event_type: str,
    data: dict[str, Any],
) -> str | None:
    """Publish an event to a Pub/Sub topic.

    Args:
        topic_name: Pub/Sub topic name
        event_type: Event type identifier
        data: Event payload

    Returns:
        Message ID if published, None on error.
    """
    client = _get_pubsub_client()
    if not client or not PROJECT_ID:
        logger.warning("⚠️ Pub/Sub unavailable — notification stored locally only")
        _store_in_app_notification(event_type, data)
        return None

    try:
        topic_path = client.topic_path(PROJECT_ID, topic_name)
        message = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data,
        }
        future = client.publish(
            topic_path,
            json.dumps(message).encode("utf-8"),
            event_type=event_type,
        )
        msg_id = future.result(timeout=5)
        logger.info(f"📨 Published to {topic_name}: {msg_id}")
        return msg_id

    except Exception as e:
        logger.error(f"❌ Pub/Sub publish error: {e}")
        _store_in_app_notification(event_type, data)
        return None


# ---------------------------------------------------------------------------
# Notification Functions
# ---------------------------------------------------------------------------

def notify_scan_complete(
    scan_id: str,
    total_issues: int,
    critical_count: int,
    doc_count: int,
) -> str | None:
    """Send notification when a scan completes."""
    data = {
        "scan_id": scan_id,
        "total_issues": total_issues,
        "critical_count": critical_count,
        "doc_count": doc_count,
        "severity": "critical" if critical_count > 0 else "info",
    }

    topic = TOPIC_CRITICAL_ALERT if critical_count > 0 else TOPIC_SCAN_COMPLETE
    return publish_event(topic, "scan.complete", data)


def notify_critical_issue(
    scan_id: str,
    issue_category: str,
    issue_message: str,
    doc_name: str = "",
) -> str | None:
    """Send immediate alert for critical issues."""
    return publish_event(
        TOPIC_CRITICAL_ALERT,
        "issue.critical",
        {
            "scan_id": scan_id,
            "category": issue_category,
            "message": issue_message[:200],
            "doc_name": doc_name,
            "severity": "critical",
        },
    )


# ---------------------------------------------------------------------------
# In-App Notifications (Firestore-backed)
# ---------------------------------------------------------------------------

def _store_in_app_notification(
    event_type: str,
    data: dict[str, Any],
):
    """Store notification in Firestore for in-app display."""
    client = _get_firestore_client()
    if not client:
        return

    try:
        timestamp = datetime.now(timezone.utc)
        doc_id = f"notif_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"

        notification = {
            "event_type": event_type,
            "timestamp": timestamp.isoformat(),
            "data": data,
            "read": False,
            "severity": data.get("severity", "info"),
        }

        client.collection(NOTIFICATIONS_COLLECTION).document(doc_id).set(notification)
    except Exception as e:
        logger.error(f"❌ In-app notification save error: {e}")


def get_unread_notifications(limit: int = 20) -> list[dict[str, Any]]:
    """Get unread in-app notifications for dashboard display."""
    client = _get_firestore_client()
    if not client:
        return []

    try:
        docs = (
            client.collection(NOTIFICATIONS_COLLECTION)
            .where("read", "==", False)
            .order_by("timestamp", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)
        return results
    except Exception as e:
        logger.error(f"❌ Notification query error: {e}")
        return []


def mark_notification_read(notification_id: str) -> bool:
    """Mark a notification as read."""
    client = _get_firestore_client()
    if not client:
        return False

    try:
        client.collection(NOTIFICATIONS_COLLECTION).document(notification_id).update(
            {"read": True}
        )
        return True
    except Exception as e:
        logger.error(f"❌ Notification update error: {e}")
        return False
