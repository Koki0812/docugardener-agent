"""
Audit logging service for DocuAlign AI.

Tracks all user actions with full audit trail:
- Review decisions (approve/deny)
- Scan executions
- Configuration changes
- System events

All events are stored in Firestore with timestamps and user context.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger("docualign.audit")

AUDIT_COLLECTION = "audit_logs"


def _get_client():
    """Lazily initialize Firestore client."""
    try:
        from google.cloud import firestore
        import os

        project = os.environ.get("GCP_PROJECT_ID", "")
        if project:
            return firestore.Client(project=project)
        return firestore.Client()
    except Exception as e:
        logger.warning(f"Firestore audit client init failed: {e}")
        return None


def log_audit_event(
    action: str,
    user: str = "system",
    resource_type: str = "",
    resource_id: str = "",
    details: Optional[dict[str, Any]] = None,
    result: str = "success",
) -> str | None:
    """Record an audit event to Firestore.

    Args:
        action: Action type (e.g. 'review.approve', 'scan.execute', 'config.update')
        user: User who performed the action
        resource_type: Type of resource (e.g. 'scan', 'issue', 'document')
        resource_id: ID of the affected resource
        details: Additional context for the action
        result: Outcome ('success', 'failure', 'partial')

    Returns:
        Audit log document ID, or None on error.
    """
    timestamp = datetime.now(timezone.utc)
    doc_id = f"audit_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"

    event = {
        "timestamp": timestamp.isoformat(),
        "action": action,
        "user": user,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "result": result,
        "details": details or {},
        "ip_address": "",  # Populated by middleware if available
    }

    # Always log locally
    logger.info(
        f"AUDIT: [{action}] user={user} resource={resource_type}/{resource_id} "
        f"result={result}"
    )

    client = _get_client()
    if not client:
        logger.warning("⚠️ Firestore unavailable — audit event logged locally only")
        return None

    try:
        doc_ref = client.collection(AUDIT_COLLECTION).document(doc_id)
        doc_ref.set(event)
        return doc_id
    except Exception as e:
        logger.error(f"❌ Audit log save error: {e}")
        return None


# ---------------------------------------------------------------------------
# Convenience functions for common audit actions
# ---------------------------------------------------------------------------

def audit_review_action(
    scan_id: str,
    issue_key: str,
    decision: str,
    reviewer: str = "admin",
    reason: str = "",
) -> str | None:
    """Log a review decision (approve/deny)."""
    return log_audit_event(
        action=f"review.{decision}",
        user=reviewer,
        resource_type="issue",
        resource_id=f"{scan_id}/{issue_key}",
        details={
            "scan_id": scan_id,
            "issue_key": issue_key,
            "decision": decision,
            "reason": reason,
        },
    )


def audit_scan_execution(
    scan_id: str,
    doc_count: int,
    trigger: str = "manual",
    user: str = "admin",
) -> str | None:
    """Log a scan execution event."""
    return log_audit_event(
        action="scan.execute",
        user=user,
        resource_type="scan",
        resource_id=scan_id,
        details={
            "doc_count": doc_count,
            "trigger": trigger,  # 'manual', 'eventarc', 'scheduled'
        },
    )


def audit_config_change(
    setting_name: str,
    old_value: str,
    new_value: str,
    user: str = "admin",
) -> str | None:
    """Log a configuration change."""
    return log_audit_event(
        action="config.update",
        user=user,
        resource_type="config",
        resource_id=setting_name,
        details={
            "old_value": old_value,
            "new_value": new_value,
        },
    )


def get_audit_trail(
    resource_type: str = "",
    resource_id: str = "",
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Retrieve audit trail, optionally filtered by resource.

    Args:
        resource_type: Filter by resource type (empty = all)
        resource_id: Filter by specific resource ID
        limit: Maximum number of entries

    Returns:
        List of audit events, newest first.
    """
    client = _get_client()
    if not client:
        return []

    try:
        query = client.collection(AUDIT_COLLECTION)

        if resource_type:
            query = query.where("resource_type", "==", resource_type)
        if resource_id:
            query = query.where("resource_id", "==", resource_id)

        docs = (
            query
            .order_by("timestamp", direction="DESCENDING")
            .limit(limit)
            .stream()
        )

        return [doc.to_dict() for doc in docs]
    except Exception as e:
        logger.error(f"❌ Audit trail query error: {e}")
        return []
