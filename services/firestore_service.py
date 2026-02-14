"""
Firestore service for DocuAlign AI.
Stores and retrieves scan results for the dashboard.
"""
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("docualign.firestore")

COLLECTION = "scan_results"


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
        logger.warning(f"Firestore client init failed: {e}")
        return None


def save_scan_result(result: dict[str, Any]) -> str | None:
    """Save a scan result to Firestore.

    Args:
        result: Scan result dict with scan_id, status, contradictions, etc.

    Returns:
        Document ID if saved, None on error.
    """
    client = _get_client()
    if not client:
        logger.warning("⚠️ Firestore unavailable — result not saved")
        return None

    scan_id = result.get("scan_id", f"scan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}")

    try:
        doc_ref = client.collection(COLLECTION).document(scan_id)
        doc_ref.set(result)
        logger.info(f"✅ Saved scan result: {scan_id}")
        return scan_id
    except Exception as e:
        logger.error(f"❌ Firestore save error: {e}")
        return None


def get_latest_results(limit: int = 10) -> list[dict[str, Any]]:
    """Retrieve the most recent scan results from Firestore.

    Args:
        limit: Maximum number of results to return.

    Returns:
        List of scan result dicts, newest first.
    """
    client = _get_client()
    if not client:
        logger.warning("⚠️ Firestore unavailable — returning empty results")
        return []

    try:
        docs = (
            client.collection(COLLECTION)
            .order_by("triggered_at", direction="DESCENDING")
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
        logger.error(f"❌ Firestore query error: {e}")
        return []


def get_scan_result(scan_id: str) -> dict[str, Any] | None:
    """Retrieve a specific scan result by ID."""
    client = _get_client()
    if not client:
        return None

    try:
        doc = client.collection(COLLECTION).document(scan_id).get()
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None
    except Exception as e:
        logger.error(f"❌ Firestore get error: {e}")
        return None


def delete_scan_result(scan_id: str) -> bool:
    """Delete a scan result from Firestore.

    Args:
        scan_id: The scan ID to delete.

    Returns:
        True if deleted, False on error.
    """
    client = _get_client()
    if not client:
        return False

    try:
        client.collection(COLLECTION).document(scan_id).delete()
        logger.info(f"🗑️ Deleted scan result: {scan_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Firestore delete error: {e}")
        return False


# ---------------------------------------------------------------------------
# Review Feedback (AI Learning Loop)
# ---------------------------------------------------------------------------

FEEDBACK_COLLECTION = "review_feedback"


def save_review_feedback(feedback: dict[str, Any]) -> str | None:
    """Save a review feedback entry to Firestore.

    Args:
        feedback: Dict with scan_id, issue_key, decision, reason,
                  issue_category, issue_detail, timestamp.

    Returns:
        Document ID if saved, None on error.
    """
    client = _get_client()
    if not client:
        logger.warning("⚠️ Firestore unavailable — feedback not saved")
        return None

    doc_id = feedback.get("issue_key", f"fb_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}")

    try:
        doc_ref = client.collection(FEEDBACK_COLLECTION).document(doc_id)
        doc_ref.set(feedback)
        logger.info(f"✅ Saved review feedback: {doc_id}")
        return doc_id
    except Exception as e:
        logger.error(f"❌ Firestore feedback save error: {e}")
        return None


def get_recent_feedback(limit: int = 20) -> list[dict[str, Any]]:
    """Retrieve recent review feedback for AI prompt enrichment.

    Args:
        limit: Maximum number of feedback entries to return.

    Returns:
        List of feedback dicts, newest first.
    """
    client = _get_client()
    if not client:
        logger.warning("⚠️ Firestore unavailable — returning empty feedback")
        return []

    try:
        docs = (
            client.collection(FEEDBACK_COLLECTION)
            .order_by("timestamp", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        logger.error(f"❌ Firestore feedback query error: {e}")
        return []
