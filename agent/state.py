"""DocuAlign AI — LangGraph state definition."""
from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """State that flows through the DocuAlign AI LangGraph pipeline.

    Nodes read and write to this shared state dict.
    """

    # ── Input ──────────────────────────────────────────────────────────
    source_file_id: str          # Drive file ID that triggered the run
    source_file_name: str        # Human-readable filename
    source_text: str             # Full text of the source document
    drive_folder_id: str         # Folder to scan

    # ── Search results ─────────────────────────────────────────────────
    related_docs: list[dict[str, Any]]  # Docs returned by Agent Builder search

    # ── Comparison outputs ─────────────────────────────────────────────
    contradictions: list[dict[str, Any]]   # Semantic contradictions found
    visual_decays: list[dict[str, Any]]    # Visual decay detections

    # ── Action outputs ─────────────────────────────────────────────────
    suggestions: list[dict[str, Any]]      # Suggested edits / comments posted
    comments_posted: int                   # Count of comments added
    feedback_context: str                  # Past reviewer feedback for AI learning

    # ── Observability ──────────────────────────────────────────────────
    logs: list[str]               # Step-by-step log for the Streamlit UI
    current_step: str             # Which node is currently executing
    error: str | None             # Last error message, if any
