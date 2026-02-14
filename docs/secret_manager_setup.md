# Secret Manager Setup Guide

This guide explains how to configure Google Cloud Secret Manager for production deployments.

## Prerequisites

- Google Cloud Project with Secret Manager API enabled
- `gcloud` CLI authenticated with appropriate permissions

## Step 1: Enable Secret Manager API

```bash
gcloud services enable secretmanager.googleapis.com --project=YOUR_PROJECT_ID
```

## Step 2: Create Secrets

Create secrets for sensitive configuration values:

```bash
# Example: Store Drive Folder ID
echo -n "YOUR_DRIVE_FOLDER_ID" | gcloud secrets create drive-folder-id \
  --data-file=- \
  --replication-policy="automatic" \
  --project=YOUR_PROJECT_ID

# Example: Store Search Engine ID
echo -n "YOUR_SEARCH_ENGINE_ID" | gcloud secrets create search-engine-id \
  --data-file=- \
  --replication-policy="automatic" \
  --project=YOUR_PROJECT_ID
```

## Step 3: Grant Access to Cloud Run Service Account

```bash
# Get your Cloud Run service account
# Default: PROJECT_NUMBER-compute@developer.gserviceaccount.com

# Grant access to all secrets
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"
```

## Step 4: Deploy with Production Flag

Set `ENV=production` environment variable in Cloud Run:

```bash
gcloud run deploy docugardener \
  --set-env-vars ENV=production \
  --project=YOUR_PROJECT_ID
```

## Supported Secrets

The following secrets can be stored in Secret Manager:

| Secret ID | Environment Variable Fallback | Description |
|-----------|-------------------------------|-------------|
| `drive-folder-id` | `DRIVE_FOLDER_ID` | Google Drive folder to monitor |
| `search-engine-id` | `SEARCH_ENGINE_ID` | Vertex AI Search engine ID |
| `search-data-store-id` | `SEARCH_DATA_STORE_ID` | Vertex AI Search data store ID |

## Local Development

For local development, **continue using `.env` files**. The application automatically falls back to environment variables when `ENV != production`.

## Troubleshooting

### Secret Not Found

```
Failed to fetch secret 'drive-folder-id' from Secret Manager: 404
```

**Solution**: Create the secret using Step 2 above.

### Permission Denied

```
Failed to fetch secret: 403 Permission denied
```

**Solution**: Grant `roles/secretmanager.secretAccessor` to your service account (Step 3).
