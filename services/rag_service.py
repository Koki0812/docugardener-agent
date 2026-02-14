"""
RAG (Retrieval-Augmented Generation) service for DocuAlign AI.

Learns from past reviewer decisions to improve detection accuracy:
- Retrieves similar past review decisions from Firestore
- Enriches Gemini prompts with historical human judgment patterns
- Reduces false positives over time via feedback loop

Architecture:
    Review Action → save_review_feedback() → Firestore
    compare_text() → get_feedback_context() → Gemini prompt enrichment
"""
import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger("docualign.rag")

FEEDBACK_COLLECTION = "review_feedback"
FEEDBACK_VECTORS_COLLECTION = "feedback_vectors"


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


def save_review_feedback(
    scan_id: str,
    issue_key: str,
    decision: str,
    reason: str = "",
    issue_category: str = "",
    issue_severity: str = "",
    issue_detail: str = "",
    reviewer: str = "admin",
) -> str | None:
    """Save a review feedback entry for RAG retrieval.

    This builds the knowledge base that Gemini uses to improve
    future contradiction detection accuracy.

    Args:
        scan_id: Parent scan ID
        issue_key: Unique issue identifier
        decision: 'approved' or 'denied'
        reason: Reviewer's explanation
        issue_category: Category of the detected issue
        issue_severity: Severity level
        issue_detail: Full description of the issue
        reviewer: Who made the decision

    Returns:
        Document ID if saved, None on error.
    """
    client = _get_client()
    if not client:
        logger.warning("⚠️ Firestore unavailable — feedback not saved")
        return None

    timestamp = datetime.now(timezone.utc)
    doc_id = f"{scan_id}_{issue_key}"

    feedback = {
        "scan_id": scan_id,
        "issue_key": issue_key,
        "decision": decision,
        "reason": reason,
        "issue_category": issue_category,
        "issue_severity": issue_severity,
        "issue_detail": issue_detail,
        "reviewer": reviewer,
        "timestamp": timestamp.isoformat(),
        # Denormalized fields for efficient querying
        "is_false_positive": decision == "denied",
        "is_valid_issue": decision == "approved",
    }

    try:
        doc_ref = client.collection(FEEDBACK_COLLECTION).document(doc_id)
        doc_ref.set(feedback)
        logger.info(f"✅ Saved RAG feedback: {doc_id} ({decision})")
        return doc_id
    except Exception as e:
        logger.error(f"❌ RAG feedback save error: {e}")
        return None


def get_feedback_context(
    category: str = "",
    limit: int = 10,
) -> str:
    """Build a feedback context string for Gemini prompt enrichment.

    Retrieves recent reviewer decisions and formats them as context
    for improving Gemini's contradiction detection accuracy.

    Args:
        category: Filter by issue category (empty = all)
        limit: Maximum number of feedback entries

    Returns:
        Formatted context string for prompt injection.
    """
    client = _get_client()
    if not client:
        return ""

    try:
        query = client.collection(FEEDBACK_COLLECTION)

        if category:
            query = query.where("issue_category", "==", category)

        docs = (
            query
            .order_by("timestamp", direction="DESCENDING")
            .limit(limit)
            .stream()
        )

        feedback_entries = [doc.to_dict() for doc in docs]

        if not feedback_entries:
            return ""

        # Build structured context
        lines = []
        approved = [f for f in feedback_entries if f.get("is_valid_issue")]
        denied = [f for f in feedback_entries if f.get("is_false_positive")]

        if approved:
            lines.append("【正しい検出の例（承認済み）】")
            for fb in approved[:5]:
                lines.append(
                    f"- カテゴリ: {fb.get('issue_category', '不明')}, "
                    f"重要度: {fb.get('issue_severity', '不明')}, "
                    f"内容: {fb.get('issue_detail', '')[:100]}"
                )

        if denied:
            lines.append("\n【誤検出の例（却下済み — 同様のケースは無視してください）】")
            for fb in denied[:5]:
                reason = fb.get("reason", "理由なし")
                lines.append(
                    f"- カテゴリ: {fb.get('issue_category', '不明')}, "
                    f"内容: {fb.get('issue_detail', '')[:100]}, "
                    f"却下理由: {reason}"
                )

        context = "\n".join(lines)
        logger.info(
            f"📚 RAG context: {len(approved)} approved, {len(denied)} denied "
            f"feedback entries loaded"
        )
        return context

    except Exception as e:
        logger.error(f"❌ RAG feedback query error: {e}")
        return ""


def get_feedback_stats() -> dict[str, Any]:
    """Get summary statistics of review feedback for dashboard display.

    Returns:
        Dict with total, approved, denied counts and top categories.
    """
    client = _get_client()
    if not client:
        return {"total": 0, "approved": 0, "denied": 0, "categories": {}}

    try:
        docs = client.collection(FEEDBACK_COLLECTION).stream()
        entries = [doc.to_dict() for doc in docs]

        approved = sum(1 for e in entries if e.get("is_valid_issue"))
        denied = sum(1 for e in entries if e.get("is_false_positive"))

        # Count by category
        categories: dict[str, int] = {}
        for e in entries:
            cat = e.get("issue_category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total": len(entries),
            "approved": approved,
            "denied": denied,
            "accuracy_rate": round(approved / len(entries) * 100, 1) if entries else 0,
            "categories": dict(sorted(categories.items(), key=lambda x: -x[1])[:5]),
        }

    except Exception as e:
        logger.error(f"❌ Feedback stats error: {e}")
        return {"total": 0, "approved": 0, "denied": 0, "categories": {}}
