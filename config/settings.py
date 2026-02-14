"""Centralized configuration for DocuAlign AI."""
import os


# Google Cloud
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
GCP_LOCATION = os.environ.get("GCP_LOCATION", "asia-northeast1")

# Vertex AI
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")

# Vertex AI Agent Builder (Discovery Engine)
SEARCH_ENGINE_ID = os.environ.get("SEARCH_ENGINE_ID", "")
SEARCH_DATA_STORE_ID = os.environ.get("SEARCH_DATA_STORE_ID", "")

# Google Drive
DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "")

# GCS (for Eventarc trigger)
GCS_BUCKET = os.environ.get("GCS_BUCKET", "hackathon4-487208-docs")

# Firestore
FIRESTORE_COLLECTION = os.environ.get("FIRESTORE_COLLECTION", "scan_results")

# App
APP_TITLE = "🛡️ DocuAlign AI"
APP_DESCRIPTION = "ドキュメントの矛盾・劣化を自動検知し、常に最新・正確な状態に保つ自律型管理エージェント"
