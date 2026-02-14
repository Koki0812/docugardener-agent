"""
Cloud Tasks integration for DocuAlign AI.

Enables asynchronous, reliable execution of long-running scan operations:
- Enqueue scan jobs to Cloud Tasks
- Automatic retries on failure
- Rate limiting for Gemini API calls
- Dead-letter queue for permanently failed tasks

Architecture:
    Dashboard → enqueue_scan() → Cloud Tasks → Cloud Run /webhook → Agent
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger("docualign.tasks")

QUEUE_ID = os.environ.get("CLOUD_TASKS_QUEUE", "docualign-scan-queue")
LOCATION = os.environ.get("GCP_LOCATION", "asia-northeast1")
PROJECT = os.environ.get("GCP_PROJECT_ID", "")
SERVICE_URL = os.environ.get("CLOUD_RUN_SERVICE_URL", "")


def _get_client():
    """Lazily initialize Cloud Tasks client."""
    try:
        from google.cloud import tasks_v2
        return tasks_v2.CloudTasksClient()
    except Exception as e:
        logger.warning(f"Cloud Tasks client init failed: {e}")
        return None


def enqueue_scan(
    doc_ids: list[str],
    trigger: str = "manual",
    priority: int = 0,
    delay_seconds: int = 0,
) -> str | None:
    """Enqueue a document scan job to Cloud Tasks.

    Args:
        doc_ids: List of document IDs to scan
        trigger: Trigger source ('manual', 'eventarc', 'scheduled')
        priority: Task priority (0=normal, 1=high)
        delay_seconds: Delay before execution (for rate limiting)

    Returns:
        Task name if enqueued, None on error.
    """
    client = _get_client()
    if not client:
        logger.warning("⚠️ Cloud Tasks unavailable — running scan synchronously")
        return None

    if not PROJECT or not SERVICE_URL:
        logger.warning("⚠️ GCP_PROJECT_ID or CLOUD_RUN_SERVICE_URL not set")
        return None

    try:
        from google.cloud import tasks_v2
        from google.protobuf import timestamp_pb2
        import datetime as dt

        parent = client.queue_path(PROJECT, LOCATION, QUEUE_ID)

        scan_id = f"scan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        payload = {
            "scan_id": scan_id,
            "doc_ids": doc_ids,
            "trigger": trigger,
            "priority": priority,
            "queued_at": datetime.now(timezone.utc).isoformat(),
        }

        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{SERVICE_URL}/webhook/scan",
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(payload).encode(),
            }
        }

        # Add delay if specified (for rate limiting)
        if delay_seconds > 0:
            d = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=delay_seconds)
            ts = timestamp_pb2.Timestamp()
            ts.FromDatetime(d)
            task["schedule_time"] = ts

        response = client.create_task(request={"parent": parent, "task": task})
        logger.info(f"✅ Enqueued scan task: {response.name}")
        return response.name

    except Exception as e:
        logger.error(f"❌ Cloud Tasks enqueue error: {e}")
        return None


def enqueue_batch_scan(
    doc_ids: list[str],
    batch_size: int = 5,
    delay_between: int = 2,
) -> list[str]:
    """Enqueue multiple scan tasks with rate limiting.

    Splits doc_ids into batches and adds delay between batches
    to respect Gemini API rate limits.

    Args:
        doc_ids: All document IDs to scan
        batch_size: Documents per batch
        delay_between: Seconds between batches

    Returns:
        List of enqueued task names.
    """
    task_names = []

    for i in range(0, len(doc_ids), batch_size):
        batch = doc_ids[i:i + batch_size]
        delay = (i // batch_size) * delay_between

        task_name = enqueue_scan(
            doc_ids=batch,
            trigger="batch",
            delay_seconds=delay,
        )
        if task_name:
            task_names.append(task_name)

    logger.info(
        f"📋 Enqueued {len(task_names)} batch scan tasks "
        f"for {len(doc_ids)} documents"
    )
    return task_names


def get_queue_stats() -> dict[str, Any]:
    """Get queue statistics for dashboard display.

    Returns:
        Dict with queue name, task count estimates, and state.
    """
    client = _get_client()
    if not client or not PROJECT:
        return {
            "queue": QUEUE_ID,
            "available": False,
            "pending": 0,
            "processing": 0,
        }

    try:
        queue_path = client.queue_path(PROJECT, LOCATION, QUEUE_ID)
        queue = client.get_queue(request={"name": queue_path})

        return {
            "queue": QUEUE_ID,
            "available": True,
            "state": queue.state.name if hasattr(queue.state, "name") else str(queue.state),
            "rate_limit": {
                "max_dispatches_per_second": queue.rate_limits.max_dispatches_per_second
                if queue.rate_limits else None,
            },
        }
    except Exception as e:
        logger.warning(f"Queue stats unavailable: {e}")
        return {
            "queue": QUEUE_ID,
            "available": False,
            "pending": 0,
            "processing": 0,
        }
