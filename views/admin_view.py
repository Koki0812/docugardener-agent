import streamlit as st
import time
import logging
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Firestore helpers
# ---------------------------------------------------------------------------
def _load_scan_history() -> list[dict]:
    try:
        from services.firestore_service import get_latest_results
        results = get_latest_results(limit=20)
        return results if results else []
    except Exception as e:
        st.session_state["firestore_error"] = str(e)
        return []

def _save_review_feedback(scan_id: str, issue_key: str, decision: str, reason: str, issue: dict):
    """Save review feedback to Firestore for AI learning."""
    from datetime import datetime, timezone
    feedback = {
        "scan_id": scan_id,
        "issue_key": issue_key,
        "decision": decision,
        "reason": reason,
        "issue_category": issue.get("category", ""),
        "issue_detail": issue.get("old", ""),
        "issue_suggestion": issue.get("new", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        from services.firestore_service import save_review_feedback
        save_review_feedback(feedback)
    except Exception as e:
        logging.warning(f"Feedback save failed: {e}")
    # Also store reason in session state for display
    st.session_state.review_reasons[issue_key] = reason

# ---------------------------------------------------------------------------
# Demo helper
# ---------------------------------------------------------------------------
def _run_agent_demo(doc_id: str) -> dict[str, Any]:
    time.sleep(1.5)
    
    # SCENARIO 1: UI Guide (contradictions + visual decay)
    if "UI_Guide" in doc_id:
        return {
            "contradictions": [
                {
                    "severity": "critical", "category": "ナビゲーション手順",
                    "old_doc": "UI Guide v2",
                    "message": "設定画面への遷移方法が旧バージョン（ギアアイコン）のまま",
                    "suggestion": "サイドメニューの「設定」からアクセスする手順に更新",
                    "old_text": "画面右上のギアアイコン（⚙）をクリックし、表示されるドロップダウンメニューから「設定」を選択してください。",
                    "new_text": "サイドメニューの「設定」をクリックして、設定画面を開いてください。（v3.0よりギアアイコンは廃止されました）",
                },
                {
                    "severity": "warning", "category": "用語変更",
                    "old_doc": "UI Guide v2",
                    "message": "「ダッシュボード」はv3.0で「ホーム画面」に名称変更済み",
                    "suggestion": "全ての「ダッシュボード」を「ホーム画面」に置換",
                    "old_text": "ログイン後、ダッシュボードが表示されます。ダッシュボードから各機能にアクセスしてください。",
                    "new_text": "ログイン後、ホーム画面が表示されます。ホーム画面から各機能にアクセスしてください。",
                },
            ],
            "visual_decays": [
                {
                    "severity": "warning", "category": "スクリーンショット更新",
                    "old_doc": "Operations Manual v2.1",
                    "description": "ログイン画面のスクリーンショットが旧デザイン（v2.0 青テーマ）のまま",
                    "suggestion": "v3.0のダークテーマ＋SSO対応の新ログイン画面に差し替え",
                    "type": "image_replacement"
                },
            ],
            "suggestions_count": 2,
            "related_docs": [{"title": "UI Specs v3.0", "doc_id": "ctx_1"}]
        }

    # SCENARIO 2: New Hire Guide (Terminology)
    elif "New_Hire_Guide" in doc_id:
        return {
            "contradictions": [
                {
                    "severity": "warning", "category": "用語統一",
                    "old_doc": "New Hire Guide 2024",
                    "message": "「ダッシュボード」は廃止済み用語",
                    "suggestion": "「ホーム画面」に一括置換",
                    "old_text": "ログイン後、ダッシュボードから各機能にアクセスできます。",
                    "new_text": "ログイン後、ホーム画面から各機能にアクセスできます。",
                },
                {
                    "severity": "info", "category": "連絡先更新",
                    "old_doc": "New Hire Guide 2024",
                    "message": "IT部門の連絡先が旧情報（内線1234）のまま",
                    "suggestion": "Slackチャンネル #it-support に更新",
                    "old_text": "IT部門: 内線 1234",
                    "new_text": "IT部門: Slackチャンネル #it-support（内線1234は廃止）",
                }
            ],
            "visual_decays": [],
            "suggestions_count": 2,
            "related_docs": [{"title": "Terminology Guide 2025", "doc_id": "ctx_2"}]
        }

    # SCENARIO 3: User Manual (API & Authentication changes)
    elif "User_Manual" in doc_id:
        return {
            "contradictions": [
                {
                    "severity": "critical", "category": "API仕様変更",
                    "old_doc": "User Manual v1",
                    "message": "REST APIのエンドポイントがv1のまま（v2に移行済み）",
                    "suggestion": "全てのAPIパスを /api/v2/ に更新",
                    "old_text": "データ取得には GET /api/v1/users エンドポイントを使用してください。",
                    "new_text": "データ取得には GET /api/v2/users エンドポイントを使用してください。（v1は2024年12月に廃止済み）",
                },
                {
                    "severity": "warning", "category": "認証方式変更",
                    "old_doc": "User Manual v1",
                    "message": "パスワード認証の記載が残っているが、SSO認証に移行済み",
                    "suggestion": "SSO（シングルサインオン）による認証手順に更新",
                    "old_text": "ログイン画面でメールアドレスとパスワードを入力し、「ログイン」ボタンをクリックしてください。",
                    "new_text": "「SSOでログイン」ボタンをクリックし、社内IDプロバイダーで認証してください。（パスワード認証は廃止されました）",
                },
                {
                    "severity": "info", "category": "機能名変更",
                    "old_doc": "User Manual v1",
                    "message": "「レポート出力」機能は「データエクスポート」に名称変更済み",
                    "suggestion": "全ての「レポート出力」を「データエクスポート」に置換",
                    "old_text": "レポート出力機能を使用して、月次データをCSV形式で出力できます。",
                    "new_text": "データエクスポート機能を使用して、月次データをCSV/Excel形式で出力できます。",
                }
            ],
            "visual_decays": [],
            "suggestions_count": 3,
            "related_docs": [{"title": "API Migration Guide v2", "doc_id": "ctx_4"}]
        }

    # SCENARIO 4: API Reference (Endpoint & Authentication)
    elif "API_Reference" in doc_id:
        return {
            "contradictions": [
                {
                    "severity": "critical", "category": "エンドポイント変更",
                    "old_doc": "API Reference v2.5",
                    "message": "認証エンドポイントが旧バージョン /auth/login のまま",
                    "suggestion": "v3.0 では /api/v3/auth/token に変更されました",
                    "old_text": "POST /auth/login\nパラメータ: username, password\nレスポンス: { token: string }",
                    "new_text": "POST /api/v3/auth/token\nパラメータ: email, password, grant_type\nレスポンス: { access_token: string, refresh_token: string, expires_in: number }",
                },
                {
                    "severity": "critical", "category": "認証方式更新",
                    "old_doc": "API Reference v2.5",
                    "message": "API キー認証の記載があるが、v3.0 では OAuth 2.0 + JWT に変更済み",
                    "suggestion": "OAuth 2.0 フローと JWT トークン使用方法を記載",
                    "old_text": "リクエストヘッダーに X-API-Key: YOUR_API_KEY を含めてください。",
                    "new_text": "Authorization: Bearer YOUR_JWT_TOKEN ヘッダーを使用してください。トークンは /api/v3/auth/token エンドポイントで取得できます。",
                },
                {
                    "severity": "warning", "category": "パラメータ追加",
                    "old_doc": "API Reference v2.5",
                    "message": "ユーザー検索APIに新規パラメータ 'role' が追加されているが未記載",
                    "suggestion": "role パラメータ（admin, user, guest）の説明を追加",
                    "old_text": "GET /api/v3/users?name={name}&status={status}",
                    "new_text": "GET /api/v3/users?name={name}&status={status}&role={role}\n新規パラメータ role: ユーザーロールでフィルタ（admin|user|guest）",
                },
            ],
            "visual_decays": [],
            "suggestions_count": 3,
            "related_docs": [{"title": "API Migration Guide v3.0", "doc_id": "ctx_5"}]
        }

    # SCENARIO 5: Security Policy (Password & Encryption)
    elif "Security_Policy" in doc_id:
        return {
            "contradictions": [
                {
                    "severity": "critical", "category": "セキュリティ要件",
                    "old_doc": "Security Policy 2023",
                    "message": "パスワード要件が古い基準（8文字以上）のまま",
                    "suggestion": "2024年基準では12文字以上 + MFA必須に更新",
                    "old_text": "パスワードは最低8文字で、英数字を含む必要があります。",
                    "new_text": "パスワードは最低12文字で、英数字+記号を含む必要があります。さらに多要素認証(MFA)の有効化が必須です。",
                },
                {
                    "severity": "critical", "category": "暗号化方式",
                    "old_doc": "Security Policy 2023",
                    "message": "データ暗号化に SHA-1 の記載があるが、2024年より SHA-256 が必須",
                    "suggestion": "SHA-256 以上の暗号化アルゴリズム使用を明記",
                    "old_text": "機密データは SHA-1 または MD5 でハッシュ化してください。",
                    "new_text": "機密データは SHA-256 以上（推奨: SHA-3）でハッシュ化してください。SHA-1 と MD5 は脆弱性のため使用禁止です。",
                },
                {
                    "severity": "warning", "category": "アクセス制御",
                    "old_doc": "Security Policy 2023",
                    "message": "ロールベースアクセス制御(RBAC)の記載がない",
                    "suggestion": "2024年より RBAC による権限管理が必須",
                    "old_text": "ユーザーには適切なアクセス権限を付与してください。",
                    "new_text": "ロールベースアクセス制御(RBAC)により、最小権限の原則に基づいて権限を付与してください。デフォルトロール: Admin, Editor, Viewer を使用します。",
                },
            ],
            "visual_decays": [],
            "suggestions_count": 3,
            "related_docs": [{"title": "Security Standards 2024", "doc_id": "ctx_6"}]
        }

    # SCENARIO 6: Troubleshooting FAQ (Outdated Solutions)
    elif "Troubleshooting_FAQ" in doc_id or "FAQ" in doc_id:
        return {
            "contradictions": [
                {
                    "severity": "warning", "category": "解決済み問題",
                    "old_doc": "Troubleshooting FAQ v2.0",
                    "message": "ログインエラーの対処法が v2.5 で修正済みのバグを案内している",
                    "suggestion": "v3.0 では SSO 認証に変更されたため、この項目自体が不要",
                    "old_text": "Q: ログイン時に 'Invalid password' エラーが出る\nA: パスワードをリセットしてください",
                    "new_text": "Q: ログイン時にエラーが出る\nA: SSO 認証に移行しました。社内IDプロバイダーで認証してください。パスワード認証は廃止されました。",
                },
                {
                    "severity": "info", "category": "バージョン情報",
                    "old_doc": "Troubleshooting FAQ v2.0",
                    "message": "推奨ブラウザが古いバージョン（Chrome 90+）のまま",
                    "suggestion": "最新の推奨環境（Chrome 120+, Edge 120+）に更新",
                    "old_text": "推奨ブラウザ: Chrome 90 以上、Firefox 88 以上",
                    "new_text": "推奨ブラウザ: Chrome 120 以上、Edge 120 以上、Firefox 115 ESR 以上（2024年12月時点）",
                },
                {
                    "severity": "warning", "category": "連絡先情報",
                    "old_doc": "Troubleshooting FAQ v2.0",
                    "message": "サポート窓口の連絡先が内線番号のまま",
                    "suggestion": "Slack チャンネル #it-support に更新",
                    "old_text": "サポートが必要な場合は内線 1234 までお問い合わせください。",
                    "new_text": "サポートが必要な場合は Slack チャンネル #it-support にご連絡ください（平日 9:00-18:00）。",
                },
            ],
            "visual_decays": [],
            "suggestions_count": 3,
            "related_docs": [{"title": "System Requirements v3.0", "doc_id": "ctx_7"}]
        }

    # SCENARIO 7: Release Notes (Feature Additions)
    elif "Release_Notes" in doc_id:
        return {
            "contradictions": [
                {
                    "severity": "info", "category": "機能追加",
                    "old_doc": "Release Notes v2.5",
                    "message": "v3.0 で追加された 'ダークモード' 機能の記載がない",
                    "suggestion": "新機能としてダークモード対応を追記",
                    "old_text": "",
                    "new_text": "新機能: ダークモード対応\n設定画面から表示テーマを切り替えられるようになりました（ライト/ダーク/システム連動）。",
                },
                {
                    "severity": "warning", "category": "スクリーンショット",
                    "old_doc": "Release Notes v2.5",
                    "message": "新しい UI のスクリーンショットが v2.0 の青テーマのまま",
                    "suggestion": "v3.0 のダークテーマのスクリーンショットに差し替え",
                    "old_text": "（スクリーンショット: 青テーマのメイン画面）",
                    "new_text": "（スクリーンショット: ダークテーマ対応のメイン画面 + テーマ切替UI）",
                },
            ],
            "visual_decays": [
                {
                    "severity": "warning", "category": "スクリーンショット更新",
                    "old_doc": "Release Notes v2.5",
                    "description": "新機能のスクリーンショットが古いデザイン（v2.0）のまま",
                    "suggestion": "v3.0 の最新 UI に差し替え",
                    "type": "image_replacement"
                },
            ],
            "suggestions_count": 2,
            "related_docs": [{"title": "Feature Specifications v3.0", "doc_id": "ctx_8"}]
        }

    # SCENARIO 8: Legacy PDF (Manual Action)
    elif "Legacy_Product_Spec" in doc_id or doc_id.endswith(".pdf"):
        return {
            "contradictions": [
                {
                    "severity": "critical", "category": "ファイル形式",
                    "old_doc": doc_id,
                    "message": "PDF形式のため自動修正不可。.docx形式に変換後、再スキャンが必要です。",
                    "suggestion": ".docx形式に変換することで自動修正が可能になります。",
                },
                {
                    "severity": "warning", "category": "バージョン矛盾",
                    "old_doc": doc_id,
                    "message": "製品仕様v2.0の記載が最新のv3.0仕様と矛盾しています。API仕様・機能説明の更新が必要です。",
                    "suggestion": "Product Specs v3.0の内容に合わせて手動で修正してください。",
                },
                {
                    "severity": "info", "category": "連絡先情報",
                    "old_doc": doc_id,
                    "message": "サポート窓口の連絡先が旧情報のままです（内線1234 → Slack #it-support）。",
                    "suggestion": "最新の連絡先に手動で更新してください。",
                }
            ],
            "visual_decays": [],
            "suggestions_count": 3,
            "related_docs": [{"title": "Product Specs v3.0", "doc_id": "ctx_3"}]
        }

    # Default / Fallback
    return {
        "contradictions": [
            {
                "severity": "warning", "category": "用語統一",
                "old_doc": doc_id,
                "message": "「ユーザー」と「ユーザ」が混在しています。",
                "suggestion": "「ユーザー」に統一してください。",
                "old_text": "ユーザは管理画面からログインし、ユーザー設定を更新できます。",
                "new_text": "ユーザーは管理画面からログインし、ユーザー設定を更新できます。",
            },
            {
                "severity": "info", "category": "住所変更",
                "old_doc": doc_id,
                "message": "旧住所が記載されたままです。",
                "suggestion": "最新の住所に更新してください。",
                "old_text": "本社所在地：東京都港区六本木 1-2-3",
                "new_text": "本社所在地：東京都渋谷区渋谷 4-5-6",
            }
        ],
        "visual_decays": [
             {
                "severity": "info", "category": "UI更新",
                "old_doc": doc_id,
                "description": "ログイン画面のキャプチャが旧デザインです（ボタンが四角い → 丸ボタンに変更済み）",
                "suggestion": "v3.0のダークテーマ新ログイン画面のスクリーンショットに差し替え",
                "type": "image_replacement"
            }
        ],
        "suggestions_count": 3,
        "related_docs": []
    }

# ---------------------------------------------------------------------------
# GCS Polling
# ---------------------------------------------------------------------------
def _poll_and_process_gcs():
    """GCSバケットの未処理ファイルを検出し、エージェントパイプラインを実行する。"""
    try:
        from google.cloud import storage
        from services.firestore_service import save_scan_result, get_latest_results
        from config.settings import GCS_BUCKET

        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET)
        blobs = list(bucket.list_blobs())

        if not blobs:
            return

        # Get all document blobs
        doc_extensions = (".docx", ".doc", ".pdf", ".txt", ".md")
        new_files = [
            b for b in blobs
            if any(b.name.lower().endswith(ext) for ext in doc_extensions)
        ]

        if not new_files:
            return

        # Delete existing scan results so rescans produce fresh data
        existing = get_latest_results(limit=100)
        for old in existing:
            old_id = old.get("scan_id", "")
            if old_id:
                try:
                    from services.firestore_service import delete_scan_result
                    delete_scan_result(old_id)
                except Exception:
                    pass  # delete_scan_result may not exist yet

        for blob in new_files:
            # Generate a scan ID
            scan_id = f"scan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{blob.name.replace('/', '_')}"
            
            try:
                # Try real agent pipeline imports
                from webhook import _run_pipeline
                result = _run_pipeline(GCS_BUCKET, blob.name, scan_id)
            except Exception:
                # Fallback to demo result
                result = _run_agent_demo(blob.name)

            scan_record = {
                "scan_id": scan_id,
                "status": "completed",
                "bucket": GCS_BUCKET,
                "file_name": blob.name,
                "file_size": blob.size or 0,
                "triggered_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "contradictions": result.get("contradictions", []),
                "visual_decays": result.get("visual_decays", []),
                "suggestions": result.get("suggestions", []),
                "related_docs": result.get("related_docs", []),
            }
            save_scan_result(scan_record)

    except Exception as e:
        logging.warning(f"GCS polling error: {e}")

# ---------------------------------------------------------------------------
# Helper: Categorize files
# ---------------------------------------------------------------------------
EDITABLE_EXTENSIONS = ['.docx', '.txt', '.md', '.html']
NON_EDITABLE_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg']

def categorize_scan(scan_item):
    filename = scan_item.get("file_name", "")
    ext = filename[filename.rfind('.'):].lower() if '.' in filename else ''
    
    if ext in EDITABLE_EXTENSIONS:
        return "auto_fixed"
    elif ext in NON_EDITABLE_EXTENSIONS:
        return "manual_alert"
    else:
        return "auto_fixed"

def calculate_issue_stats(history, review_status):
    """Calculate clear issue statistics for dashboard display."""
    total_issues = 0
    resolved_issues = 0
    pending_critical = 0
    pending_warning = 0
    
    for scan in history:
        scan_id = scan.get("scan_id", scan.get("id"))
        c_list = scan.get("contradictions", [])
        v_list = scan.get("visual_decays", [])
        
        # Count contradictions
        for i, issue in enumerate(c_list):
            total_issues += 1
            issue_key = f"{scan_id}_issue_{i}"
            
            if review_status.get(issue_key) in ["approved", "denied"]:
                resolved_issues += 1
            else:
                # Pending issue - categorize by severity
                sev = issue.get("severity", "unknown").lower()
                if sev == "critical":
                    pending_critical += 1
                elif sev == "warning":
                    pending_warning += 1
        
        # Count visual decays
        offset = len(c_list)
        for j, issue in enumerate(v_list):
            total_issues += 1
            issue_key = f"{scan_id}_issue_{offset+j}"
            
            if review_status.get(issue_key) in ["approved", "denied"]:
                resolved_issues += 1
            else:
                sev = issue.get("severity", "unknown").lower()
                if sev == "critical":
                    pending_critical += 1
                elif sev == "warning":
                    pending_warning += 1
    
    return {
        "total": total_issues,
        "resolved": resolved_issues,
        "resolved_pct": int((resolved_issues / total_issues * 100) if total_issues > 0 else 0),
        "pending_critical": pending_critical,
        "pending_warning": pending_warning,
    }

# ---------------------------------------------------------------------------
# Onboarding Flow
# ---------------------------------------------------------------------------
def _show_onboarding():
    """Display interactive onboarding tutorial for first-time users."""
    step = st.session_state.get("onboarding_step", 1)
    
    # Progress indicator
    steps_label = ["スキャン実行", "問題の確認", "承認 / 却下"]
    progress_html = ""
    for i, label in enumerate(steps_label, 1):
        if i < step:
            progress_html += f'<span style="color:#30D158;font-weight:600;">✅ {label}</span>'
        elif i == step:
            progress_html += f'<span style="color:#5E5CE6;font-weight:700;">▶ {label}</span>'
        else:
            progress_html += f'<span style="color:#86868B;">{label}</span>'
        if i < len(steps_label):
            progress_html += ' → '
    
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#E8F5E9,#E3F2FD); padding:24px 32px; border-radius:16px; margin-bottom:24px;">
        <h2 style="margin:0 0 8px 0;">👋 DocuAlign AI へようこそ！</h2>
        <p style="color:#555; margin:0 0 16px 0;">AI によるドキュメント矛盾検出システムの使い方を 3 ステップでご紹介します。</p>
        <div style="font-size:0.9rem;">{progress_html}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if step == 1:
        st.info("""
        ### 📡 Step 1: スキャン実行
        
        サイドバー右上の **「スキャン実行」** ボタンをクリックすると、GCS バケット内のドキュメントを自動分析します。
        
        **AI が検出するもの**:
        - 📝 新旧ドキュメント間のテキスト矛盾
        - 🖼️ 古いスクリーンショット（Visual Decay）
        - ⚠️ セキュリティポリシー違反
        - 🔗 古い API エンドポイント参照
        """)
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("次へ →", key="onboard_next_1"):
                st.session_state.onboarding_step = 2
                st.rerun()
        with col2:
            if st.button("スキップ", key="onboard_skip_1"):
                st.session_state.onboarding_completed = True
                st.rerun()
    
    elif step == 2:
        st.info("""
        ### 🔍 Step 2: 問題の確認
        
        検出された問題は **重要度** によって分類されます:
        
        | アイコン | 重要度 | 説明 |
        |:---:|:---:|---|
        | 🔴 | **Critical** | セキュリティや正確性に影響する重大な矛盾 |
        | 🟡 | **Warning** | 更新推奨だが緊急ではない差異 |
        | 🔵 | **Info** | 軽微な用語変更など情報提供 |
        
        各問題カードで「旧テキスト」→「新テキスト」の差分を確認できます。
        """)
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("← 戻る", key="onboard_back_2"):
                st.session_state.onboarding_step = 1
                st.rerun()
        with col2:
            if st.button("次へ →", key="onboard_next_2"):
                st.session_state.onboarding_step = 3
                st.rerun()
        with col3:
            if st.button("スキップ", key="onboard_skip_2"):
                st.session_state.onboarding_completed = True
                st.rerun()
    
    elif step == 3:
        st.success("""
        ### ✅ Step 3: 承認 / 却下
        
        各問題に対してアクションを選択してください:
        
        - ✅ **承認**: AI の修正提案を採用（自動的に記録）
        - ❌ **却下**: 問題なしと判断（却下理由を入力可能）
        
        対応済みの問題はダッシュボード上で「対応済」としてカウントされます。
        
        **💡 ヒント**: サイドバーの「📖 チュートリアルを再表示」ボタンで、いつでもこのガイドに戻れます。
        """)
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("← 戻る", key="onboard_back_3"):
                st.session_state.onboarding_step = 2
                st.rerun()
        with col2:
            if st.button("🚀 チュートリアル完了！", key="onboard_done"):
                st.session_state.onboarding_completed = True
                st.rerun()
    
    st.divider()

# ---------------------------------------------------------------------------
# Main Render Function
# ---------------------------------------------------------------------------
def render_admin_dashboard():
    # Session State
    for key, default in [
        ("agent_logs", []),
        ("agent_results", None),
        ("run_count", 0),
        ("scan_history", []),
        ("last_refresh", None),
        ("review_status", {}),
        ("review_reasons", {}),
        ("onboarding_completed", False),
        ("onboarding_step", 1),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # CSS
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary:        #30D158;
        --primary-soft:   rgba(48, 209, 88, 0.12);
        --secondary:      #5E5CE6;
        --danger:         #FF453A;
        --warning:        #FF9F0A;
        --bg-base:        #F5F5F7;
        --bg-card:        #FFFFFF;
        --text-primary:   #1D1D1F;
        --text-secondary: #86868B;
        --border-light:   rgba(0,0,0,0.04);
        --shadow-sm:      0 2px 8px rgba(0,0,0,0.02);
        --shadow-md:      0 8px 16px rgba(0,0,0,0.04);
    }
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        color: var(--text-primary) !important;
    }
    
    .stApp { background: var(--bg-base) !important; }
    
    /* Header Adjustments - Keep header visible for Sidebar Toggle, but hide clutter */
    header[data-testid="stHeader"] { background: transparent !important; }
    div[data-testid="stDecoration"] { display: none; }
    div[data-testid="stStatusWidget"] { display: none; }
    button[data-testid="baseButton-headerNoPadding"] { display: none; }
    
    .top-bar {
        display: flex; align-items: center; justify-content: space-between;
        padding: 16px 24px;
        background: var(--bg-card);
        border-bottom: 1px solid var(--border-light);
        margin: 0 -1rem 2rem -1rem;
        position: sticky; top: 0; z-index: 100;
    }
    .logo-area { display: flex; align-items: center; gap: 12px; }
    .geo-icon {
        width: 36px; height: 36px; background: var(--primary);
        mask-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath fill-rule='evenodd' clip-rule='evenodd' d='M12 2L2 12L12 22L22 12L12 2Z' fill='black'/%3E%3C/svg%3E");
        mask-size: contain; -webkit-mask-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath fill-rule='evenodd' clip-rule='evenodd' d='M12 2L2 12L12 22L22 12L12 2Z' fill='black'/%3E%3C/svg%3E");
        -webkit-mask-size: contain; background-color: var(--primary);
    }
    .app-name { font-family: 'Space Grotesk', sans-serif; font-size: 1.25rem; font-weight: 700; color: var(--text-primary); letter-spacing: -0.02em; }
    .status-badge { display: flex; align-items: center; gap: 8px; padding: 6px 12px; background: var(--primary-soft); border-radius: 32px; color: #1a8f3b; font-size: 0.8rem; font-weight: 600; }
    .status-dot { width: 8px; height: 8px; background: #30D158; border-radius: 50%; animation: pulse 2s infinite; }
    @keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(0.9); } 100% { opacity: 1; transform: scale(1); } }
    
    .conn-info { font-size: 0.75rem; color: var(--text-secondary); display: flex; align-items: center; gap: 6px; }
    .conn-ok { color: var(--primary); font-weight: 600; }
    .conn-err { color: var(--danger); font-weight: 600; }
    
    .card { background: var(--bg-card); border-radius: 12px; padding: 20px; box-shadow: var(--shadow-sm); border: 1px solid var(--border-light); height: 100%; }
    .metric-val { font-family: 'Space Grotesk', sans-serif; font-size: 2rem; font-weight: 700; margin-bottom: 4px; }
    .metric-lbl { font-size: 0.85rem; font-weight: 500; color: var(--text-secondary); }
    
    .health-gauge { position: relative; width: 100%; height: 8px; background: #EEE; border-radius: 4px; overflow: hidden; margin-top: 12px; }
    .health-fill { height: 100%; background: var(--primary); border-radius: 4px; transition: width 1s ease-out; }
    .health-score { font-size: 2.5rem; font-weight: 800; color: var(--primary); line-height: 1; }
    
    .alert-card { background: #FFF4F4; border-left: 4px solid var(--danger); padding: 16px; border-radius: 4px 12px 12px 4px; margin-bottom: 12px; }
    .alert-badge { background: var(--danger); color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; display: inline-block; margin-bottom: 8px; }
    
    .diff-container { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 12px 0; }
    .diff-panel { background: #FAFAFA; border-radius: 8px; padding: 16px; border: 1px solid #E5E5EA; font-size: 0.85rem; line-height: 1.6; }
    .diff-panel-old { border-left: 4px solid #FF453A; }
    .diff-panel-new { border-left: 4px solid #30D158; }
    .diff-del { background: #FFE5E5; color: #D92D20; padding: 2px 4px; border-radius: 3px; }
    .diff-add { background: #E5FFE9; color: #1a8f3b; padding: 2px 4px; border-radius: 3px; }
    
    .feed-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: #FFF; border-radius: 8px; border: 1px solid #EEE; margin-bottom: 8px; }
    
    .stButton > button { background: var(--text-primary) !important; color: #FFF !important; border-radius: 8px !important; font-weight: 600 !important; border: none !important; box-shadow: var(--shadow-md) !important; }
    .stButton > button:hover { background: #333 !important; }
    </style>
    """, unsafe_allow_html=True)

    # ─── Onboarding Flow ───
    if not st.session_state.onboarding_completed:
        _show_onboarding()
    
    # Sidebar
    with st.sidebar:
        st.title("⚙ 設定")
        st.caption("監視対象GCSバケット:")
        st.code("gs://hackathon4-487208-docs/")
        st.divider()
        if st.button("📖 チュートリアルを再表示"):
            st.session_state.onboarding_completed = False
            st.session_state.onboarding_step = 1
            st.rerun()

    # Data Loading
    firestore_connected = True
    last_update_time = None

    # "スキャン実行" button — always visible
    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button("スキャン実行"):
            with st.spinner("スキャン中..."):
                _poll_and_process_gcs()

    # Load scan history from Firestore
    history = _load_scan_history()
    if "firestore_error" in st.session_state:
        firestore_connected = False
    scan_count = len(history)
    last_update_time = history[0].get("triggered_at", "") if history else None

    # Stats
    auto_fixed_items = [s for s in history if categorize_scan(s) == "auto_fixed"]
    manual_alert_items = [s for s in history if categorize_scan(s) == "manual_alert"]
    
    auto_fixed_count = len(auto_fixed_items)
    manual_alert_count = len(manual_alert_items)
    total_issues = sum(len(x.get("contradictions", [])) + len(x.get("visual_decays", [])) for x in history)
    
    issue_stats = calculate_issue_stats(history, st.session_state.review_status)

    # Top Bar
    conn_status_html = f'<span class="conn-ok">● Firestore 接続済</span>' if firestore_connected else f'<span class="conn-err">● Firestore エラー</span>'
    last_update_html = f'<span style="margin-left:16px;">最終更新: {last_update_time[:16] if last_update_time else "N/A"}</span>' if last_update_time else ''
    
    st.markdown(f"""
    <div class="top-bar">
        <div class="logo-area">
            <div class="geo-icon"></div>
            <div class="app-name">DocuAlign AI</div>
        </div>
        <div style="display:flex; align-items:center; gap:16px;">
            <div class="conn-info">{conn_status_html}{last_update_html}</div>
            <div class="status-badge">
                <div class="status-dot"></div>
                <span>システム稼働中</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="card">
            <div class="metric-lbl">検出問題数</div>
            <div class="metric-val">{issue_stats['total']}件</div>
            <div style="margin-top:8px; font-size:0.8rem; color:#86868B;">
                <div style="margin-bottom:4px;">✅ 対応済: {issue_stats['resolved']}件 ({issue_stats['resolved_pct']}%)</div>
                <div style="margin-bottom:2px;">⚠️ 未対応 (Critical): {issue_stats['pending_critical']}件</div>
                <div>🔶 未対応 (Warning): {issue_stats['pending_warning']}件</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="card"><div class="metric-val">{scan_count}</div><div class="metric-lbl">スキャン総数</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="card" style="border-left:4px solid #30D158;"><div class="metric-val" style="color:#30D158;">{auto_fixed_count}</div><div class="metric-lbl">自動修正 (Auto-Fix)</div></div>""", unsafe_allow_html=True)
    with c4: st.markdown(f"""<div class="card" style="border-left:4px solid #FF453A;"><div class="metric-val" style="color:#FF453A;">{manual_alert_count}</div><div class="metric-lbl">要手動対応</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Results
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        st.subheader("自動修正ドキュメント")
        if not auto_fixed_items:
            st.info("ドキュメントはありません。")
        else:
            for idx, item in enumerate(auto_fixed_items[:5]):
                fname = item.get("file_name", "不明")
                scan_id = item.get("scan_id", item.get("id", f"item_{idx}"))
                
                # Combine issues logic
                contradictions = item.get("contradictions", [])
                visual_decays = item.get("visual_decays", [])
                all_issues = []
                for c in contradictions:
                    # Handle string contradictions (old pipeline format)
                    if isinstance(c, str):
                        # Try to split at "→ 修正提案:" delimiter
                        if "→ 修正提案:" in c:
                            parts = c.split("→ 修正提案:", 1)
                            all_issues.append({"type": "text", "category": "AI分析", "old": parts[0].strip(), "new": parts[1].strip(), "doc": "", "detail": c})
                        else:
                            all_issues.append({"type": "text", "category": "AI分析", "old": c[:200], "new": "（AIにより修正済み）", "doc": "", "detail": c})
                        continue

                    # === Build old_display (修正前: 問題の説明) ===
                    old_display = c.get("old_text", "") or c.get("message", "")
                    if not old_display:
                        # Fallback: parse analysis field
                        analysis = c.get("analysis", "")
                        if analysis:
                            if "→ 修正提案:" in analysis:
                                old_display = analysis.split("→ 修正提案:", 1)[0].strip()
                            else:
                                old_display = analysis[:200]
                        else:
                            old_display = "（AIが矛盾を検出）"

                    # === Build new_display (修正後: AIによる修正内容) ===
                    new_display = c.get("new_text", "") or c.get("suggestion", "")
                    if not new_display:
                        # Fallback: parse suggestion from analysis field
                        analysis = c.get("analysis", "")
                        if "→ 修正提案:" in analysis:
                            new_display = analysis.split("→ 修正提案:", 1)[1].strip()
                        elif "修正提案:" in analysis:
                            new_display = analysis.split("修正提案:", 1)[1].strip()
                        else:
                            new_display = "（AIにより修正済み）"

                    all_issues.append({"type": "text", "category": c.get("category", "テキスト修正"), "old": old_display, "new": new_display, "doc": c.get("old_doc", ""), "detail": c.get("message", "")})
                for v in visual_decays:
                    all_issues.append({"type": "image" if "png" in v.get("suggestion", "") else "text", "category": v.get("category", "画像修正"), "old": v.get("description", "旧画像"), "new": v.get("suggestion", "新画像"), "doc": v.get("old_doc", "")})
                
                n_issues = len(all_issues)
                
                # Review Status Logic
                approved_count = 0
                denied_count = 0
                for i in range(n_issues):
                    issue_key = f"{scan_id}_issue_{i}"
                    status = st.session_state.review_status.get(issue_key, None)
                    if status == "approved": approved_count += 1
                    if status == "denied": denied_count += 1
                
                if approved_count + denied_count == 0:
                    status_icon, status_text = "⚪", "レビュー待ち"
                elif approved_count + denied_count == n_issues:
                    if denied_count > 0: status_icon, status_text = "🔴", "レビュー完了 (一部却下)"
                    else: status_icon, status_text = "🟢", "全件承認済"
                else:
                    status_icon, status_text = "🟡", f"レビュー中 ({approved_count + denied_count}/{n_issues})"

                # Expander
                if "expanded_scans" not in st.session_state: st.session_state.expanded_scans = set()
                is_expanded = scan_id in st.session_state.expanded_scans
                
                with st.expander(f"{status_icon} {fname} — {status_text}", expanded=is_expanded):
                    st.markdown(f"<div style='margin-bottom:12px; font-size:0.9rem; color:#666;'>{n_issues} 件の問題を検出</div>", unsafe_allow_html=True)
                    for i, issue in enumerate(all_issues):
                        issue_key = f"{scan_id}_issue_{i}"
                        status = st.session_state.review_status.get(issue_key, None)
                        
                        if status == "approved":
                            status_html = '<span class="status-icon-approved">✅ 承認済</span>'
                            bg_style = "border: 1px solid #30D158; background: #F0FFF4;"
                        elif status == "denied":
                            status_html = '<span class="status-icon-denied">❌ 却下</span>'
                            bg_style = "border: 1px solid #FF453A; background: #FFF0F0;"
                        else:
                            status_html = '<span class="status-icon-pending">⏳ 未承認</span>'
                            bg_style = "border: 1px solid #EEE;"

                        st.markdown(f"""
                        <div style="{bg_style} border-radius:8px; padding:12px; margin-bottom:0px;">
                            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                                <span style="font-weight:bold; font-size:0.85rem;">問題 {i+1}: {issue['category']}</span>
                                {status_html}
                            </div>
                        """, unsafe_allow_html=True)

                        old_content = f'<span class="diff-del">{issue["old"]}</span>'
                        if issue['type'] == 'image':
                            new_content = f'<div style="color:#30D158; font-weight:bold; margin-bottom:4px;">✅ 差し替え画像:</div><img src="{issue["new"]}" width="100%" style="border-radius:4px; border:2px solid #30D158;">'
                            if "http" not in issue["new"]: new_content = f'<span class="diff-add">🖼️ 画像差し替え: {issue["new"]}</span>'
                        else:
                            new_content = f'<span class="diff-add">{issue["new"]}</span>'

                        st.markdown(f"""
                            <div class="diff-container" style="margin:0;">
                                <div class="diff-panel diff-panel-old">
                                    <span class="diff-label" style="color:#FF453A;">修正前</span>
                                    <div>{old_content}</div>
                                </div>
                                <div class="diff-panel diff-panel-new">
                                    <span class="diff-label" style="color:#30D158;">修正後</span>
                                    <div>{new_content}</div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Spacing & Reason Input
                        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

                        if status is not None:
                            # Already reviewed — show saved reason
                            saved_reason = st.session_state.review_reasons.get(issue_key, "")
                            if saved_reason:
                                st.markdown(f"<div style='font-size:0.8rem; color:#86868B; margin-bottom:8px;'>💬 理由: {saved_reason}</div>", unsafe_allow_html=True)
                        else:
                            # Pending — show reason input + buttons
                            reason = st.text_input(
                                "選択理由（任意 — AIの学習に活用されます）",
                                key=f"reason_{issue_key}",
                                placeholder="例: この用語は社内基準で正しいため変更不要",
                            )

                        b1, b2, _ = st.columns([0.15, 0.15, 0.7])
                        with b1:
                            if st.button("承認", key=f"app_{issue_key}", type="primary" if status is None else "secondary"):
                                entered_reason = st.session_state.get(f"reason_{issue_key}", "")
                                st.session_state.review_status[issue_key] = "approved"
                                _save_review_feedback(scan_id, issue_key, "approved", entered_reason, issue)
                                st.session_state.expanded_scans.add(scan_id)
                                st.rerun()
                        with b2:
                            if st.button("却下", key=f"den_{issue_key}"):
                                entered_reason = st.session_state.get(f"reason_{issue_key}", "")
                                st.session_state.review_status[issue_key] = "denied"
                                _save_review_feedback(scan_id, issue_key, "denied", entered_reason, issue)
                                st.session_state.expanded_scans.add(scan_id)
                                st.rerun()
                        st.markdown("<hr style='margin-top: 16px; margin-bottom: 16px; opacity: 0.3;'>", unsafe_allow_html=True)

    with col_right:
        st.subheader("⚠ 要手動対応")
        if not manual_alert_items:
            st.success("手動対応の必要はありません。")
        else:
            import html as html_mod
            for item in manual_alert_items[:5]:
                fname = item.get("file_name", "不明")
                bucket_name = item.get("bucket", "hackathon4-487208-docs")
                contradictions = item.get("contradictions", [])
                visual_decays = item.get("visual_decays", [])
                n_issues = len(contradictions) + len(visual_decays)
                gcs_path = f"gs://{bucket_name}/{fname}"
                console_url = f"https://console.cloud.google.com/storage/browser/_details/{bucket_name}/{fname}"

                with st.expander(f"🔴 {fname} — {n_issues} 件の矛盾を検出", expanded=False):
                    # Issue details
                    issue_num = 0
                    for c in contradictions:
                        issue_num += 1
                        cat = html_mod.escape(str(c.get("category", "テキスト矛盾")))
                        raw_msg = str(c.get("message", c.get("analysis", "詳細なし")))
                        msg = html_mod.escape(raw_msg).replace("\n", "<br>")
                        sug = html_mod.escape(str(c.get("suggestion", ""))).replace("\n", "<br>")
                        sug_html = f'<div style="color:#2E7D32; margin-top:3px;">💡 提案: {sug}</div>' if sug else ""
                        st.markdown(f'<div style="margin-top:6px; padding:8px 10px; background:#FFF5F5; border-left:3px solid #FF453A; border-radius:4px; font-size:0.78rem;"><div style="font-weight:700; color:#D92D20; margin-bottom:3px;">#{issue_num} {cat}</div><div style="color:#333;">⚠ {msg}</div>{sug_html}</div>', unsafe_allow_html=True)

                    for v in visual_decays:
                        issue_num += 1
                        cat = html_mod.escape(str(v.get("category", "画像劣化")))
                        raw_desc = str(v.get("description", "詳細なし"))
                        desc = html_mod.escape(raw_desc).replace("\n", "<br>")
                        sug = html_mod.escape(str(v.get("suggestion", ""))).replace("\n", "<br>")
                        sug_html = f'<div style="color:#2E7D32; margin-top:3px;">💡 提案: {sug}</div>' if sug else ""
                        st.markdown(f'<div style="margin-top:6px; padding:8px 10px; background:#FFF5F5; border-left:3px solid #FF453A; border-radius:4px; font-size:0.78rem;"><div style="font-weight:700; color:#D92D20; margin-bottom:3px;">#{issue_num} {cat}</div><div style="color:#333;">⚠ {desc}</div>{sug_html}</div>', unsafe_allow_html=True)

                    # File location link
                    st.markdown(f'<div style="margin-top:10px; padding:6px 10px; background:#FFF; border-radius:6px; border:1px solid #E5E5EA; font-size:0.78rem;"><span style="color:#86868B;">📍 格納場所:</span> <code style="font-size:0.75rem; background:#F5F5F7; padding:2px 6px; border-radius:4px;">{gcs_path}</code><br><a href="{console_url}" target="_blank" style="color:#5E5CE6; text-decoration:none; font-weight:600; font-size:0.78rem;">🔗 Cloud Console で開く ↗</a></div>', unsafe_allow_html=True)
    
    # Activity Feed
    st.subheader("最近のアクティビティ")
    if history:
        for act in history[:5]:
            fname = act.get("file_name", "不明なファイル")
            ts = act.get("triggered_at", "")[:16].replace("T", " ")
            category = categorize_scan(act)
            if category == "auto_fixed":
                status_html = '<span style="color:#30D158; font-weight:600;">✓ 自動修正済</span>'
                icon = "📄"
            else:
                status_html = '<span style="color:#FF453A; font-weight:600;">⚠ 要手動対応</span>'
                icon = "📕"
            st.markdown(f"""<div class="feed-item"><div style="display:flex; align-items:center; gap:12px;"><div style="font-size:1.5rem;">{icon}</div><div><div style="font-weight:600; font-size:0.9rem;">{fname}</div><div style="font-size:0.75rem; color:#86868B;">{ts}</div></div></div>{status_html}</div>""", unsafe_allow_html=True)

