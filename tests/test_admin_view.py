"""Tests for admin_view helper functions — demo scenarios and issue stats."""
import pytest


class TestRunAgentDemo:
    """Tests for _run_agent_demo scenario coverage."""

    def _get_demo(self):
        from views.admin_view import _run_agent_demo
        return _run_agent_demo

    def test_ui_guide_scenario(self):
        demo = self._get_demo()
        result = demo("UI_Guide_v2")
        assert "contradictions" in result
        assert "visual_decays" in result
        assert len(result["contradictions"]) >= 2
        assert any(c["severity"] == "critical" for c in result["contradictions"])

    def test_new_hire_scenario(self):
        demo = self._get_demo()
        result = demo("NewHire_Guide")
        assert len(result["contradictions"]) >= 1

    def test_user_manual_scenario(self):
        demo = self._get_demo()
        result = demo("User_Manual_v3")
        assert len(result["contradictions"]) >= 2

    def test_api_reference_scenario(self):
        demo = self._get_demo()
        result = demo("API_Reference_v3")
        assert len(result["contradictions"]) >= 3
        # Should have critical endpoint changes
        assert any(c["severity"] == "critical" for c in result["contradictions"])

    def test_security_policy_scenario(self):
        demo = self._get_demo()
        result = demo("Security_Policy_2024")
        assert len(result["contradictions"]) >= 3
        crits = [c for c in result["contradictions"] if c["severity"] == "critical"]
        assert len(crits) >= 2  # SHA-1 and password are critical

    def test_troubleshooting_faq_scenario(self):
        demo = self._get_demo()
        result = demo("Troubleshooting_FAQ_v2")
        assert len(result["contradictions"]) >= 3

    def test_faq_alias(self):
        demo = self._get_demo()
        result = demo("FAQ_Internal")
        assert "contradictions" in result

    def test_release_notes_scenario(self):
        demo = self._get_demo()
        result = demo("Release_Notes_v3")
        assert len(result["contradictions"]) >= 2
        assert len(result["visual_decays"]) >= 1

    def test_legacy_pdf_scenario(self):
        demo = self._get_demo()
        result = demo("Legacy_Product_Spec.pdf")
        assert "contradictions" in result
        assert "visual_decays" in result

    def test_unknown_doc_fallback(self):
        demo = self._get_demo()
        result = demo("Unknown_Document_xyz")
        assert "contradictions" in result
        assert isinstance(result["contradictions"], list)

    def test_all_scenarios_have_required_keys(self):
        """All scenarios must return contradictions, visual_decays, suggestions_count, related_docs."""
        demo = self._get_demo()
        doc_ids = [
            "UI_Guide_v2",
            "NewHire_Guide",
            "User_Manual_v3",
            "API_Reference_v3",
            "Security_Policy_2024",
            "Troubleshooting_FAQ_v2",
            "Release_Notes_v3",
            "Legacy_Product_Spec.pdf",
        ]
        for doc_id in doc_ids:
            result = demo(doc_id)
            assert "contradictions" in result, f"Missing contradictions for {doc_id}"
            assert "visual_decays" in result, f"Missing visual_decays for {doc_id}"
            assert "suggestions_count" in result, f"Missing suggestions_count for {doc_id}"
            assert "related_docs" in result, f"Missing related_docs for {doc_id}"


class TestCalculateIssueStats:
    """Tests for calculate_issue_stats."""

    def _get_stats(self):
        from views.admin_view import calculate_issue_stats
        return calculate_issue_stats

    def test_empty_history(self):
        stats = self._get_stats()
        result = stats([], {})
        assert result["total"] == 0
        assert result["resolved"] == 0
        assert result["resolved_pct"] == 0
        assert result["pending_critical"] == 0
        assert result["pending_warning"] == 0

    def test_all_resolved(self):
        stats = self._get_stats()
        history = [
            {
                "scan_id": "s1",
                "contradictions": [
                    {"severity": "critical", "category": "test"}
                ],
                "visual_decays": [],
            }
        ]
        review_status = {"s1_issue_0": "approved"}
        result = stats(history, review_status)
        assert result["total"] == 1
        assert result["resolved"] == 1
        assert result["resolved_pct"] == 100
        assert result["pending_critical"] == 0

    def test_mixed_status(self):
        stats = self._get_stats()
        history = [
            {
                "scan_id": "s1",
                "contradictions": [
                    {"severity": "critical", "category": "nav"},
                    {"severity": "warning", "category": "term"},
                ],
                "visual_decays": [
                    {"severity": "warning", "category": "img"},
                ],
            }
        ]
        review_status = {"s1_issue_0": "approved"}  # Only first resolved
        result = stats(history, review_status)
        assert result["total"] == 3
        assert result["resolved"] == 1
        assert result["pending_critical"] == 0  # critical was resolved
        assert result["pending_warning"] == 2  # 2 warnings pending


class TestCategorizeScan:
    """Tests for categorize_scan."""

    def _get_categorize(self):
        from views.admin_view import categorize_scan
        return categorize_scan

    def test_editable_doc(self):
        """Google Doc (editable) should be categorized as auto_fixed."""
        cat = self._get_categorize()
        scan = {"file_name": "guide.gdoc"}
        assert cat(scan) == "auto_fixed"

    def test_non_editable_pdf(self):
        """PDF (non-editable) should be categorized as manual_alert."""
        cat = self._get_categorize()
        scan = {"file_name": "spec.pdf"}
        assert cat(scan) == "manual_alert"

    def test_unknown_extension(self):
        """Unknown extension defaults to auto_fixed."""
        cat = self._get_categorize()
        scan = {"file_name": "readme.txt"}
        assert cat(scan) == "auto_fixed"

    def test_no_extension(self):
        """No extension defaults to auto_fixed."""
        cat = self._get_categorize()
        scan = {"file_name": "README"}
        assert cat(scan) == "auto_fixed"
