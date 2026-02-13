"""Google Drive service — file listing and download."""
from __future__ import annotations

import logging
from typing import Any

from googleapiclient.discovery import build
from google.auth import default

logger = logging.getLogger(__name__)


def _get_drive_service():
    """Build the Drive v3 API client."""
    creds, _ = default(scopes=["https://www.googleapis.com/auth/drive.readonly"])
    return build("drive", "v3", credentials=creds)


def list_recent_files(folder_id: str, max_results: int = 10) -> list[dict[str, Any]]:
    """List the most recently modified files in *folder_id*."""
    service = _get_drive_service()
    query = f"'{folder_id}' in parents and trashed = false"
    resp = (
        service.files()
        .list(
            q=query,
            orderBy="modifiedTime desc",
            pageSize=max_results,
            fields="files(id, name, mimeType, modifiedTime, webViewLink)",
        )
        .execute()
    )
    files = resp.get("files", [])
    logger.info("Found %d files in folder %s", len(files), folder_id)
    return files


def get_file_content(file_id: str) -> bytes:
    """Download the raw bytes of a Drive file."""
    service = _get_drive_service()
    return service.files().get_media(fileId=file_id).execute()


def export_google_doc(doc_id: str, mime_type: str = "text/plain") -> str:
    """Export a Google Doc to the given MIME type and return as text."""
    service = _get_drive_service()
    content = service.files().export(fileId=doc_id, mimeType=mime_type).execute()
    if isinstance(content, bytes):
        return content.decode("utf-8")
    return content
