# 設定
$PROJECT_ID = "hackathon4-487208"
$REGION = "asia-northeast1"
$SERVICE_NAME = "docugardener-agent"

Write-Host ">> Deploying to Cloud Run..." -ForegroundColor Green

# 現在のディレクトリをプロジェクトルートに設定
$PROJECT_ROOT = $PSScriptRoot

# gcloud コマンド実行
gcloud run deploy $SERVICE_NAME `
    --source $PROJECT_ROOT `
    --region $REGION `
    --allow-unauthenticated `
    --project $PROJECT_ID

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n>> Deployment successful!" -ForegroundColor Green
    Write-Host "Service URL: https://$SERVICE_NAME-444765795202.$REGION.run.app"
}
else {
    Write-Host "`n>> Deployment failed!" -ForegroundColor Red
    exit 1
}
