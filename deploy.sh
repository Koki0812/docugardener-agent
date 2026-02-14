#!/bin/bash
# DocuAlign AI — Cloud Run deployment script
# Usage: bash deploy.sh <PROJECT_ID> [REGION]

set -euo pipefail

PROJECT_ID="${1:?Usage: bash deploy.sh <PROJECT_ID> [REGION]}"
REGION="${2:-us-central1}"
SERVICE_NAME="docugardener-agent"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🛡️ DocuAlign AI — Deploying to Cloud Run"
echo "   Project:  ${PROJECT_ID}"
echo "   Region:   ${REGION}"
echo "   Service:  ${SERVICE_NAME}"
echo ""

# 1. Enable required APIs
echo "📦 Enabling required APIs..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    aiplatform.googleapis.com \
    discoveryengine.googleapis.com \
    drive.googleapis.com \
    docs.googleapis.com \
    --project="${PROJECT_ID}"

# 2. Build and push container image
echo "🐳 Building container image..."
gcloud builds submit \
    --project="${PROJECT_ID}" \
    --tag="${IMAGE_NAME}" \
    .

# 3. Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --image="${IMAGE_NAME}" \
    --platform=managed \
    --allow-unauthenticated \
    --port=8080 \
    --memory=1Gi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=3 \
    --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID},GCP_LOCATION=${REGION}" \
    --timeout=300

# 4. Get the URL
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --format="value(status.url)")

echo ""
echo "✅ Deployment complete!"
echo "🛡️ DocuAlign AI is live at:"
echo "   ${SERVICE_URL}"
echo ""
