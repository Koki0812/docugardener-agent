# DocuGardener Agent — Cloud Run deployment script (PowerShell)
# Usage: .\deploy.ps1 -ProjectId "YOUR_PROJECT_ID" [-Region "us-central1"]

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,

    [string]$Region = "us-central1"
)

$ErrorActionPreference = "Stop"
$ServiceName = "docugardener-agent"
$ImageName = "gcr.io/$ProjectId/$ServiceName"

Write-Host ""
Write-Host "🌿 DocuGardener Agent — Deploying to Cloud Run" -ForegroundColor Green
Write-Host "   Project:  $ProjectId"
Write-Host "   Region:   $Region"
Write-Host "   Service:  $ServiceName"
Write-Host ""

# 1. Enable required APIs
Write-Host "📦 Enabling required APIs..." -ForegroundColor Cyan
gcloud services enable `
    run.googleapis.com `
    cloudbuild.googleapis.com `
    aiplatform.googleapis.com `
    discoveryengine.googleapis.com `
    drive.googleapis.com `
    docs.googleapis.com `
    --project=$ProjectId
if ($LASTEXITCODE -ne 0) { throw "Failed to enable APIs" }

# 2. Build and push container image
Write-Host "🐳 Building container image..." -ForegroundColor Cyan
gcloud builds submit `
    --project=$ProjectId `
    --tag=$ImageName `
    .
if ($LASTEXITCODE -ne 0) { throw "Failed to build container image" }

# 3. Deploy to Cloud Run
Write-Host "🚀 Deploying to Cloud Run..." -ForegroundColor Cyan
gcloud run deploy $ServiceName `
    --project=$ProjectId `
    --region=$Region `
    --image=$ImageName `
    --platform=managed `
    --allow-unauthenticated `
    --port=8080 `
    --memory=1Gi `
    --cpu=1 `
    --min-instances=0 `
    --max-instances=3 `
    --set-env-vars="GCP_PROJECT_ID=$ProjectId,GCP_LOCATION=$Region" `
    --timeout=300
if ($LASTEXITCODE -ne 0) { throw "Failed to deploy to Cloud Run" }

# 4. Get the URL
$ServiceUrl = gcloud run services describe $ServiceName `
    --project=$ProjectId `
    --region=$Region `
    --format="value(status.url)"

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "🌿 DocuGardener Agent is live at:" -ForegroundColor Green
Write-Host "   $ServiceUrl" -ForegroundColor Yellow
Write-Host ""
