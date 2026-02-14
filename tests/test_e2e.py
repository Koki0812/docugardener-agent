"""E2E tests for DocuAlign AI main user flows.

Tests the complete flow without external dependencies
by exercising the demo mode path that runs entirely in-memory.
"""
import pytest


class TestScanAndReviewFlow:
    """End-to-end test of the primary user journey: scan → review → approve."""

    def test_full_demo_scan_flow(self):
        """Complete scan of multiple documents returns valid results."""
        from views.admin_view import _run_agent_demo

        doc_ids = [
            "UI_Guide_v2",
            "API_Reference_v3",
            "Security_Policy_2024",
        ]

        all_results = {}
        for doc_id in doc_ids:
            result = _run_agent_demo(doc_id)
            all_results[doc_id] = result

            # Every result must have the required structure
            assert "contradictions" in result
            assert "visual_decays" in result
            assert "suggestions_count" in result
            assert "related_docs" in result
            assert isinstance(result["contradictions"], list)

        # Verify we scanned all docs
        assert len(all_results) == 3

        # Critical scenarios should have critical issues
        api_crits = [
            c for c in all_results["API_Reference_v3"]["contradictions"]
            if c["severity"] == "critical"
        ]
        assert len(api_crits) >= 1, "API Reference must flag critical endpoint changes"

    def test_issue_stats_after_review(self):
        """Issue stats correctly reflect review decisions."""
        from views.admin_view import _run_agent_demo, calculate_issue_stats

        # Step 1: Run scan
        result = _run_agent_demo("UI_Guide_v2")
        scan_id = "e2e_test_scan"

        history = [{
            "scan_id": scan_id,
            "contradictions": result["contradictions"],
            "visual_decays": result["visual_decays"],
        }]

        # Step 2: No reviews yet → all pending
        stats_before = calculate_issue_stats(history, {})
        total = stats_before["total"]
        assert total > 0
        assert stats_before["resolved"] == 0

        # Step 3: Approve first issue
        review_status = {f"{scan_id}_issue_0": "approved"}
        stats_after = calculate_issue_stats(history, review_status)
        assert stats_after["resolved"] == 1
        assert stats_after["resolved_pct"] > 0

    def test_categorize_doc_types(self):
        """Different doc types are correctly categorized."""
        from views.admin_view import categorize_scan

        editable = categorize_scan({"file_name": "guide.gdoc"})
        non_editable = categorize_scan({"file_name": "spec.pdf"})

        assert editable == "auto_fixed"
        assert non_editable == "manual_alert"


class TestAuditServiceFlow:
    """E2E test of audit trail creation and retrieval."""

    def test_audit_event_structure(self):
        """Audit events have required fields."""
        from services.audit_service import log_audit_event

        # Without Firestore, should still log locally and return None
        result = log_audit_event(
            action="review.approve",
            user="test_user",
            resource_type="issue",
            resource_id="scan_001/c_0",
            details={"decision": "approved"},
        )
        # Returns None without Firestore, but doesn't crash
        assert result is None or isinstance(result, str)

    def test_convenience_functions_dont_crash(self):
        """All audit convenience functions handle missing Firestore gracefully."""
        from services.audit_service import (
            audit_review_action,
            audit_scan_execution,
            audit_config_change,
            get_audit_trail,
        )

        # These should all return None (no Firestore) without crashing
        audit_review_action("scan1", "c_0", "approved", "admin", "looks correct")
        audit_scan_execution("scan1", 5, "manual")
        audit_config_change("model", "1.5-pro", "2.0-flash")

        trail = get_audit_trail()
        assert isinstance(trail, list)


class TestRAGServiceFlow:
    """E2E test of RAG feedback save and context generation."""

    def test_feedback_save_without_firestore(self):
        """Feedback save handles missing Firestore gracefully."""
        from services.rag_service import save_review_feedback

        result = save_review_feedback(
            scan_id="scan1",
            issue_key="c_0",
            decision="approved",
            issue_category="terminology",
            issue_detail="Dashboard terminology change",
        )
        assert result is None or isinstance(result, str)

    def test_feedback_context_returns_string(self):
        """get_feedback_context always returns a string."""
        from services.rag_service import get_feedback_context

        context = get_feedback_context(category="terminology")
        assert isinstance(context, str)

    def test_feedback_stats_returns_dict(self):
        """get_feedback_stats always returns valid dict structure."""
        from services.rag_service import get_feedback_stats

        stats = get_feedback_stats()
        assert "total" in stats
        assert "approved" in stats
        assert "denied" in stats


class TestNotificationServiceFlow:
    """E2E test of notification service."""

    def test_scan_complete_notification(self):
        """Scan completion notification handles missing Pub/Sub gracefully."""
        from services.notification_service import notify_scan_complete

        result = notify_scan_complete(
            scan_id="scan1",
            total_issues=5,
            critical_count=2,
            doc_count=3,
        )
        # Returns None without Pub/Sub, but doesn't crash
        assert result is None or isinstance(result, str)

    def test_unread_notifications(self):
        """Unread notification query returns list."""
        from services.notification_service import get_unread_notifications

        notifications = get_unread_notifications()
        assert isinstance(notifications, list)


class TestTaskQueueServiceFlow:
    """E2E test of Cloud Tasks integration."""

    def test_enqueue_without_cloud_tasks(self):
        """Enqueue handles missing Cloud Tasks gracefully."""
        from services.task_queue_service import enqueue_scan

        result = enqueue_scan(doc_ids=["doc1", "doc2"], trigger="manual")
        assert result is None or isinstance(result, str)

    def test_queue_stats(self):
        """Queue stats returns valid structure."""
        from services.task_queue_service import get_queue_stats

        stats = get_queue_stats()
        assert "queue" in stats
        assert "available" in stats


class TestLoggingServiceFlow:
    """E2E test of structured logging."""

    def test_setup_and_log(self):
        """Setup + structured logging works end-to-end."""
        from services.logging_service import (
            setup_logging,
            log_scan_event,
            log_api_call,
        )

        setup_logging()
        log_scan_event("test_scan", {"doc_id": "e2e_test"})
        log_api_call("gemini", "compare_text", 500.0, True)
        # No assertion needed — test passes if no exception


class TestRetryFlow:
    """E2E test of retry + circuit breaker integration."""

    def test_retry_with_circuit_breaker(self):
        """Retry decorator works with circuit breaker."""
        from utils.retry import retry_with_backoff, CircuitBreaker

        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def api_call():
            nonlocal call_count
            call_count += 1
            return breaker.call(lambda: f"result_{call_count}")

        result = api_call()
        assert result == "result_1"
        assert breaker.state == "closed"
