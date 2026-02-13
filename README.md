# 🌿 DocuGardener Agent

> 検索されるのを待たない。自ら動き、知識の森を「剪定」する自律型庭師AI。

**Google Cloud Japan AI Hackathon Vol.4 出展作品**

## 🎯 プロジェクト概要

### 課題
企業のマニュアル・手順書は、システム更新のたびに内容が陳腐化します。しかし、数百ページに及ぶドキュメント群から矛盾箇所を人手で探すのは非現実的です。

### ソリューション
DocuGardener Agent は、ドキュメント更新をトリガーに **自律的に** 古い資料との矛盾を検出し、修正提案まで行う **Agentic AI** です。

### コア機能

| 機能 | 説明 | 技術 |
|---|---|---|
| ✂️ **Semantic Pruning** | 新旧ドキュメントの意味的矛盾を検出・剪定 | Gemini 1.5 Pro (2M Context) |
| 🖼️ **Visual Freshness** | マニュアル内スクリーンショットの鮮度をチェック | Gemini Multimodal |
| ✅ **One-Click Fix** | Google Docsにコメント/提案を自動書き込み | Google Docs API |

## 🏗️ アーキテクチャ

```
Google Drive (Trigger)
       │
       ▼
┌─────────────┐
│ fetch_source │ ← Google Docs API
└──────┬──────┘
       ▼
┌──────────────┐
│search_related│ ← Vertex AI Agent Builder
└──────┬───────┘
       ▼
┌─────────────────┐
│Semantic Pruning  │ ← Gemini 1.5 Pro (2M Context)
└───────┬─────────┘
        ▼
┌─────────────────┐
│Visual Freshness  │ ← Gemini Multimodal
└───────┬─────────┘
        ▼
┌──────────────┐
│One-Click Fix │ → Google Docs コメント
└──────────────┘
```

## 🛠️ 技術スタック

| レイヤー | 技術 |
|---|---|
| **フロントエンド** | Streamlit |
| **Agent Logic** | LangGraph (Python) |
| **AI Model** | Vertex AI Gemini 1.5 Pro |
| **Search / RAG** | Vertex AI Agent Builder |
| **API連携** | Google Drive API, Google Docs API |
| **実行環境** | Google Cloud Run |
| **言語** | Python 3.11 |

## 📁 プロジェクト構造

```
├── app.py                  # Streamlit ダッシュボード
├── Dockerfile              # Cloud Run コンテナ
├── requirements.txt        # 依存パッケージ
├── deploy.sh               # デプロイスクリプト (bash)
├── deploy.ps1              # デプロイスクリプト (PowerShell)
├── config/
│   └── settings.py         # 環境変数ベースの設定
├── services/
│   ├── drive_service.py    # Google Drive API
│   ├── docs_service.py     # Google Docs API
│   ├── vertex_ai_service.py# Gemini (テキスト + マルチモーダル)
│   └── search_service.py   # Agent Builder 検索
└── agent/
    ├── state.py            # LangGraph AgentState
    ├── nodes.py            # パイプラインノード
    └── graph.py            # LangGraph StateGraph
```

## 🚀 デプロイ方法

### Cloud Shell から:
```bash
gcloud config set project YOUR_PROJECT_ID
bash deploy.sh YOUR_PROJECT_ID asia-northeast1
```

### PowerShell から:
```powershell
.\deploy.ps1 -ProjectId "YOUR_PROJECT_ID" -Region "asia-northeast1"
```

## 💻 ローカル実行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📄 ライセンス

MIT License
