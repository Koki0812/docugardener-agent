# 自動デプロイ設定ガイド

## 方法1: GitHub Actions による CI/CD（推奨）

`git push` するだけで自動ビルド・デプロイされます。

### 手順

#### 1. Workload Identity 設定（初回のみ）

```bash
# Cloud Shell で実行
export PROJECT_ID=hackathon4-487208
export REPO_OWNER=Koki0812
export REPO_NAME=docugardener-agent

# Workload Identity Pool 作成
gcloud iam workload-identity-pools create "github-pool" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --display-name="GitHub Actions Pool"

# Provider 作成
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Service Account 作成
gcloud iam service-accounts create github-actions-sa \
  --display-name="GitHub Actions Service Account"

# 権限付与
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Workload Identity 紐付け
gcloud iam service-accounts add-iam-policy-binding \
  github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe ${PROJECT_ID} --format='value(projectNumber)')/locations/global/workloadIdentityPools/github-pool/attribute.repository/${REPO_OWNER}/${REPO_NAME}"
```

#### 2. GitHub Actions Workflow ファイル作成

ローカルで `.github/workflows/deploy.yml` を作成：

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches:
      - main

env:
  PROJECT_ID: hackathon4-487208
  REGION: asia-northeast1
  SERVICE_NAME: docugardener-agent

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    permissions:
      contents: read
      id-token: write
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: 'projects/${{ secrets.GCP_PROJECT_NUMBER }}/locations/global/workloadIdentityPools/github-pool/providers/github-provider'
          service_account: 'github-actions-sa@${{ env.PROJECT_ID }}.iam.gserviceaccount.com'
      
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2
      
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy ${{ env.SERVICE_NAME }} \
            --source . \
            --region ${{ env.REGION }} \
            --allow-unauthenticated \
            --project ${{ env.PROJECT_ID }}
```

#### 3. GitHub Secrets 設定

GitHub リポジトリの Settings > Secrets and variables > Actions で以下を追加：

```
GCP_PROJECT_NUMBER: <プロジェクト番号>
```

プロジェクト番号の取得：
```bash
gcloud projects describe hackathon4-487208 --format='value(projectNumber)'
```

#### 4. デプロイ

```bash
git add .
git commit -m "Enable GitHub Actions deployment"
git push origin main
```

→ GitHub Actions が自動的に Cloud Run にデプロイします！

---

## 方法2: ローカルスクリプトによる自動デプロイ

GitHub Actions を使わない場合、PowerShell スクリプトで自動化できます。

### `deploy_to_cloudrun.ps1`

```powershell
# 設定
$PROJECT_ID = "hackathon4-487208"
$REGION = "asia-northeast1"
$SERVICE_NAME = "docugardener-agent"

Write-Host ">> Deploying to Cloud Run..." -ForegroundColor Green

# 現在のディレクトリをプロジェクトルートに設定
$PROJECT_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path

# gcloud コマンド実行
gcloud run deploy $SERVICE_NAME `
  --source $PROJECT_ROOT `
  --region $REGION `
  --allow-unauthenticated `
  --project $PROJECT_ID

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n>> Deployment successful!" -ForegroundColor Green
    Write-Host "Service URL: https://$SERVICE_NAME-444765795202.$REGION.run.app"
} else {
    Write-Host "`n>> Deployment failed!" -ForegroundColor Red
    exit 1
}
```

使い方：
```powershell
.\deploy_to_cloudrun.ps1
```

---

## 推奨：GitHub Actions を使用

**メリット:**
- ✅ コード変更を `git push` するだけで自動デプロイ
- ✅ デプロイ履歴が GitHub Actions に記録される
- ✅ 複数人での開発に対応
- ✅ ローカル環境に依存しない

**デメリット:**
- 初回設定がやや複雑（Workload Identity 設定）

初回設定さえ完了すれば、以降は `git push` だけで済むため、非常に効率的です。
