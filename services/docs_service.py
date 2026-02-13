"""Google Docs service — read, extract images, and write comments/suggestions."""
from __future__ import annotations

import logging
from typing import Any

from googleapiclient.discovery import build
from google.auth import default

logger = logging.getLogger(__name__)


def _get_docs_service():
    """Build the Docs v1 API client."""
    creds, _ = default(scopes=["https://www.googleapis.com/auth/documents"])
    return build("docs", "v1", credentials=creds)


def _get_drive_service():
    """Build the Drive v3 API client (for comments)."""
    creds, _ = default(scopes=["https://www.googleapis.com/auth/drive"])
    return build("drive", "v3", credentials=creds)


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------

def get_document(doc_id: str) -> dict[str, Any]:
    """Return the full Docs API document resource."""
    service = _get_docs_service()
    doc = service.documents().get(documentId=doc_id).execute()
    logger.info("Fetched document: %s", doc.get("title"))
    return doc


def get_document_text(doc_id: str) -> str:
    """Extract plain text from a Google Doc."""
    doc = get_document(doc_id)
    text_parts: list[str] = []
    for element in doc.get("body", {}).get("content", []):
        paragraph = element.get("paragraph")
        if paragraph:
            for run in paragraph.get("elements", []):
                text_run = run.get("textRun")
                if text_run:
                    text_parts.append(text_run.get("content", ""))
    return "".join(text_parts)


def extract_images(doc_id: str) -> list[dict[str, Any]]:
    """Extract inline image information from a Google Doc.

    Returns a list of dicts with keys: ``object_id``, ``content_uri``,
    ``width``, ``height``.
    """
    doc = get_document(doc_id)
    images: list[dict[str, Any]] = []
    inline_objects = doc.get("inlineObjects", {})
    for obj_id, obj in inline_objects.items():
        props = (
            obj.get("inlineObjectProperties", {})
            .get("embeddedObject", {})
        )
        image_props = props.get("imageProperties", {})
        images.append(
            {
                "object_id": obj_id,
                "content_uri": image_props.get("contentUri", ""),
                "source_uri": image_props.get("sourceUri", ""),
                "width": props.get("size", {}).get("width", {}).get("magnitude"),
                "height": props.get("size", {}).get("height", {}).get("magnitude"),
            }
        )
    logger.info("Extracted %d images from doc %s", len(images), doc_id)
    return images


# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------

def add_comment(doc_id: str, content: str, quoted_text: str = "") -> dict[str, Any]:
    """Add a comment to a Google Doc via the Drive API.

    If *quoted_text* is provided it will anchor the comment to that text.
    """
    drive = _get_drive_service()
    body: dict[str, Any] = {"content": content}
    if quoted_text:
        body["quotedFileContent"] = {"value": quoted_text}
    comment = (
        drive.comments()
        .create(fileId=doc_id, body=body, fields="id,content,createdTime")
        .execute()
    )
    logger.info("Created comment %s on doc %s", comment["id"], doc_id)
    return comment
