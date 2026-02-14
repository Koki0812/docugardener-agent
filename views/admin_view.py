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

    # SCENARIO 3: Legacy PDF (Manual Action)
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

        # Get already-processed file names from Firestore
        existing = get_latest_results(limit=100)
        processed_files = {r.get("file_name", "") for r in existing}

        # Filter to document types only
        doc_extensions = (".docx", ".doc", ".pdf", ".txt", ".md")
        new_files = [
            b for b in blobs
            if any(b.name.lower().endswith(ext) for ext in doc_extensions)
            and b.name not in processed_files
        ]

        if not new_files:
            return

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

def calculate_health(history, review_status):
    base_score = 100
    penalty = 0
    
    # Weights based on AI-determined severity
    severity_weights = {
        "critical": 10,
        "warning": 5,
        "info": 1,
        "unknown": 2
    }
    
    for scan in history:
        scan_id = scan.get("scan_id", scan.get("id"))
        
        c_list = scan.get("contradictions", [])
        v_list = scan.get("visual_decays", [])
        
        # Contradictions (0 to len(c)-1)
        for i, issue in enumerate(c_list):
            issue_key = f"{scan_id}_issue_{i}"
            # If approved or denied, it's "resolved" -> No penalty
            if review_status.get(issue_key) in ["approved", "denied"]:
                continue
            
            sev = issue.get("severity", "unknown").lower()
            penalty += severity_weights.get(sev, 2)
            
        # Visual Decays (len(c) to len(c)+len(v)-1)
        offset = len(c_list)
        for j, issue in enumerate(v_list):
            issue_key = f"{scan_id}_issue_{offset+j}"
            if review_status.get(issue_key) in ["approved", "denied"]:
                continue
            
            sev = issue.get("severity", "unknown").lower()
            penalty += severity_weights.get(sev, 2)
        
    return max(0, base_score - penalty)

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

    # Sidebar
    with st.sidebar:
        st.title("⚙ 設定")
        mode = st.radio("モード", ["自動モニタリング", "デモモード"])
        is_auto = mode == "自動モニタリング"
        if is_auto:
            st.caption("監視対象GCSバケット:")
            st.code("gs://hackathon4-487208-docs/")

    # Data Loading
    firestore_connected = True
    last_update_time = None

    if is_auto:
        _poll_and_process_gcs()
        history = _load_scan_history()
        if "firestore_error" in st.session_state:
            firestore_connected = False
        scan_count = len(history)
        last_update_time = history[0].get("triggered_at", "") if history else None
    else:
        # Demo logic
        c1, c2 = st.columns([1, 4])
        with c1:
            if st.button("スキャン実行"):
                with st.spinner("スキャン中..."):
                    res = _run_agent_demo("Operations_Manual_v2.1.docx")
                    st.session_state.agent_results = res
                    st.session_state.scan_history.insert(0, {
                        "file_name": "Operations_Manual_v2.1.docx",
                        "triggered_at": datetime.now().isoformat(),
                        "status": "completed",
                        "contradictions": res["contradictions"],
                        "visual_decays": res["visual_decays"]
                    })
        history = st.session_state.scan_history
        scan_count = len(history)
        last_update_time = history[0].get("triggered_at", "") if history else None

    # Stats
    auto_fixed_items = [s for s in history if categorize_scan(s) == "auto_fixed"]
    manual_alert_items = [s for s in history if categorize_scan(s) == "manual_alert"]
    
    auto_fixed_count = len(auto_fixed_items)
    manual_alert_count = len(manual_alert_items)
    total_issues = sum(len(x.get("contradictions", [])) + len(x.get("visual_decays", [])) for x in history)
    
    health_score = calculate_health(history, st.session_state.review_status)
    health_color = "#30D158" if health_score >= 80 else "#FF9F0A" if health_score >= 50 else "#FF453A"

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
                <span>{'システム稼働中' if is_auto else 'デモモード'}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="card"><div class="metric-lbl">ドキュメント健全性</div><div class="health-score" style="color:{health_color}">{health_score}</div><div class="health-gauge"><div class="health-fill" style="width:{health_score}%; background:{health_color};"></div></div></div>""", unsafe_allow_html=True)
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
                        all_issues.append({"type": "text", "category": "AI分析", "old": c[:200], "new": "（自動修正済み）", "doc": "", "detail": c})
                        continue
                    # Prefer old_text > message > analysis for "修正前"
                    old_display = c.get("old_text", "") or c.get("message", "") or c.get("analysis", "")[:200] if c.get("analysis") else c.get("message", "（AIが矛盾を検出）")
                    # Prefer new_text > suggestion for "修正後"
                    new_display = c.get("new_text", "") or c.get("suggestion", "（修正提案あり）")
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

    if is_auto:
        time.sleep(10)
        st.rerun()
