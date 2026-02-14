# Troubleshooting Guide

このガイドでは、DocuAlign AI で発生する可能性のある一般的な問題と解決方法を説明します。

---

## 📋 目次

- [Firestore 関連エラー](#firestore-関連エラー)
- [Gemini API エラー](#gemini-api-エラー)
- [Google Drive エラー](#google-drive-エラー)
- [デプロイエラー](#デプロイエラー)
- [ローカル実行エラー](#ローカル実行エラー)

---

## Firestore 関連エラー

### ❌ Error: `Failed to connect to Firestore`

**原因**:
- Firestore API が有効化されていない
- サービスアカウントに権限がない
- プロジェクト ID が間違っている

**解決方法**:

1. **Firestore API を有効化**:
```bash
gcloud services enable firestore.googleapis.com --project=YOUR_PROJECT_ID
```

2. **Firestore データベースを作成** (初回のみ):
```bash
# GCP Console で Firestore を開き、「ネイティブモード」でデータベースを作成
# または CLI で:
gcloud firestore databases create --region=asia-northeast1
```

3. **サービスアカウントに権限を付与**:
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT" \
  --role="roles/datastore.user"
```

4. **環境変数を確認**:
```bash
echo $GCP_PROJECT_ID
# 正しいプロジェクト ID が表示されることを確認
```

---

## Gemini API エラー

### ❌ Error: `403 Permission Denied`

**原因**: Vertex AI API が有効化されていない、または権限不足

**解決方法**:

1. **Vertex AI API を有効化**:
```bash
gcloud services enable aiplatform.googleapis.com --project=YOUR_PROJECT_ID
```

2. **サービスアカウントに権限を付与**:
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT" \
  --role="roles/aiplatform.user"
```

### ❌ Error: `429 Resource Exhausted` (Quota Exceeded)

**原因**: API リクエスト数がクォータ上限に達した

**解決方法**:

1. **現在のクォータを確認**:
   - [GCP Console > IAM & Admin > Quotas](https://console.cloud.google.com/iam-admin/quotas)
   - 「Vertex AI API」で検索

2. **クォータ上限の引き上げをリクエスト**:
   - Quotas ページで該当クォータを選択
   - 「EDIT QUOTAS」をクリック
   - 新しい上限値を入力して送信

3. **一時的な対処**:
   - 数分待ってから再試行
   - リクエスト頻度を下げる

### ❌ Error: `Invalid API Key`

**原因**: API キーが正しく設定されていない

**解決方法**:

1. **.env ファイルを確認**:
```bash
cat .env | grep GCP_PROJECT_ID
# 正しいプロジェクト ID が表示されることを確認
```

2. **Secret Manager の設定を確認** (本番環境):
```bash
gcloud secrets versions access latest --secret="YOUR_SECRET_NAME"
```

---

## Google Drive エラー

### ❌ Error: `Drive folder not found`

**原因**: DRIVE_FOLDER_ID が間違っている、またはアクセス権限がない

**解決方法**:

1. **フォルダ ID を確認**:
   - Google Drive で対象フォルダを開く
   - URL から ID を取得: `https://drive.google.com/drive/folders/【ここがID】`

2. **サービスアカウントに共有**:
   - フォルダを右クリック → 「共有」
   - サービスアカウントのメールアドレスを追加
   - 権限: 「閲覧者」以上

3. **.env を更新**:
```bash
DRIVE_FOLDER_ID=【正しいフォルダID】
```

---

## デプロイエラー

### ❌ Error: `Cloud Run service deployment failed`

**原因**: Docker ビルドエラー、権限不足、リソース不足など

**解決方法**:

1. **ログを確認**:
```bash
gcloud run services describe docugardener --region=asia-northeast1
gcloud logging read "resource.type=cloud_run_revision" --limit=50
```

2. **よくある原因と対処**:

   **ケース 1: ビルドエラー**
   ```bash
   # ローカルで Docker ビルドをテスト
   docker build -t test-build .
   ```

   **ケース 2: メモリ不足**
   ```bash
   # メモリ上限を増やす
   gcloud run services update docugardener \
     --memory=2Gi \
     --region=asia-northeast1
   ```

   **ケース 3: タイムアウト**
   ```bash
   # タイムアウトを延長
   gcloud run services update docugardener \
     --timeout=300 \
     --region=asia-northeast1
   ```

### ❌ Error: `Container failed to start`

**原因**: entrypoint.sh の実行エラー、ポート設定ミス

**解決方法**:

1. **entrypoint.sh の権限を確認**:
```bash
ls -la entrypoint.sh
# -rwxr-xr-x (実行権限があることを確認)
```

2. **ローカルで Docker コンテナをテスト**:
```bash
docker run -p 8501:8501 -p 8080:8080 test-build
```

3. **ポート設定を確認**:
```bash
# Cloud Run はポート 8080 を期待
# entrypoint.sh で Streamlit が 8501、Flask が 8080 で起動していることを確認
```

---

## ローカル実行エラー

### ❌ Error: `ModuleNotFoundError: No module named 'streamlit'`

**原因**: 依存パッケージがインストールされていない

**解決方法**:

```bash
# 仮想環境を作成して有効化
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージをインストール
pip install -r requirements.txt
```

### ❌ Error: `Streamlit app won't load, showing white screen`

**原因**: ブラウザキャッシュ、ポート競合

**解決方法**:

1. **ブラウザキャッシュをクリア**:
   - Ctrl + Shift + Delete (Windows/Linux)
   - Cmd + Shift + Delete (Mac)

2. **別のポートで起動**:
```bash
streamlit run app.py --server.port=8502
```

3. **既存プロセスを終了**:
```bash
# Windows
netstat -ano | findstr :8501
taskkill /PID [プロセスID] /F

# Linux/Mac
lsof -ti:8501 | xargs kill
```

---

## 🐛 デバッグのヒント

### ログレベルを上げる

```python
# app.py の先頭に追加
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Streamlit のデバッグモード

```bash
streamlit run app.py --logger.level=debug
```

### Cloud Run のログをリアルタイム表示

```bash
gcloud logging tail "resource.type=cloud_run_revision" --format=json
```

---

## 📞 サポート

上記で解決しない場合:

1. **GitHub Issues**: [プロジェクトの Issue ページ](https://github.com/Koki0812/docugardener-agent/issues)
2. **Stack Overflow**: タグ `google-cloud-run`, `vertex-ai`, `streamlit`
3. **Google Cloud サポート**: [GCP サポート](https://cloud.google.com/support)

---

## 🔗 関連ドキュメント

- [Architecture Documentation](./architecture.md)
- [Secret Manager Setup](./secret_manager_setup.md)
- [Deployment Procedure](./deployment_procedure.md)
