"""Centralized configuration for DocuAlign AI."""
import os
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Secret Manager Integration (for production)
# ---------------------------------------------------------------------------

def get_secret(secret_id: str, default: str = "") -> str:
    """
    Retrieve secret from Google Cloud Secret Manager.
    
    Falls back to environment variables for local development.
    Set ENV=production to use Secret Manager.
    
    Args:
        secret_id: Secret name in Secret Manager
        default: Default value if secret not found
        
    Returns:
        Secret value or default
    """
    # Local development: use environment variables
    if os.getenv("ENV") != "production":
        return os.getenv(secret_id.upper().replace("-", "_"), default)
    
    # Production: use Secret Manager
    try:
        from google.cloud import secretmanager
        
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.environ.get("GCP_PROJECT_ID")
        
        if not project_id:
            logger.warning("GCP_PROJECT_ID not set, falling back to env vars")
            return os.getenv(secret_id.upper().replace("-", "_"), default)
        
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    
    except Exception as e:
        logger.warning(f"Failed to fetch secret '{secret_id}' from Secret Manager: {e}")
        return os.getenv(secret_id.upper().replace("-", "_"), default)


# Google Cloud
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
GCP_LOCATION = os.environ.get("GCP_LOCATION", "asia-northeast1")

# Vertex AI
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")

# Vertex AI Agent Builder (Discovery Engine)
SEARCH_ENGINE_ID = get_secret("search-engine-id", "")
SEARCH_DATA_STORE_ID = get_secret("search-data-store-id", "")

# Google Drive
DRIVE_FOLDER_ID = get_secret("drive-folder-id", "")

# GCS (for Eventarc trigger)
GCS_BUCKET = os.environ.get("GCS_BUCKET", "hackathon4-487208-docs")

# Firestore
FIRESTORE_COLLECTION = os.environ.get("FIRESTORE_COLLECTION", "scan_results")

# App
APP_TITLE = "🛡️ DocuAlign AI"
APP_DESCRIPTION = "ドキュメントの矛盾・劣化を自動検知し、常に最新・正確な状態に保つ自律型管理エージェント"
