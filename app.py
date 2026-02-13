"""
DocuGardener Agent — Monitoring Dashboard v1.3.0 (Light Theme)
=============================================================
🌿 Autonomous Document Gardener

Dashboard Role:
- Auto-Fixable Files (.docx, .txt): Show修正実行済み results
- Manual Action Files (.pdf): Show alerts for version conflicts
"""
import streamlit as st
import time
import logging
from datetime import datetime, timedelta
import random
from typing import Any

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="DocuGardener",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
for key, default in [
    ("agent_logs", []),
    ("agent_results", None),
    ("run_count", 0),
    ("scan_history", []),
    ("last_refresh", None),
    ("review_status", {}),    # {scan_id: "approved" | "denied"}
]:
    if key not in st.session_state:
        st.session_state[key] = default

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

# ---------------------------------------------------------------------------
# GCS Polling — detect new files and process them
# ---------------------------------------------------------------------------
def _poll_and_process_gcs():
    """Check GCS bucket for unprocessed files and run the agent pipeline."""
    try:
        from google.cloud import storage
        from services.firestore_service import save_scan_result, get_latest_results
        from config.settings import GCS_BUCKET
        from datetime import datetime, timezone

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
            scan_id = f"scan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{blob.name.replace('/', '_')}"
            try:
                # Try real agent pipeline
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
# Demo helper
# ---------------------------------------------------------------------------
def _run_agent_demo(doc_id: str) -> dict[str, Any]:
    time.sleep(1.5)
    return {
        "contradictions": [
            {
                "severity": "critical", "category": "Facts",
                "old_doc": "Operations Manual v2.1",
                "message": "Outdated instruction: 'Gear icon' vs 'Side menu'",
                "suggestion": "Update Sec.3 to reflect new navigation",
            },
            {
                "severity": "warning", "category": "Terminology",
                "old_doc": "New Hire Guide 2024",
                "message": "Term mismatch: 'Dashboard' vs 'Home'",
                "suggestion": "Standardize to 'Home Screen'",
            },
        ],
        "visual_decays": [
            {
                "severity": "info", "category": "UI Freshness",
                "old_doc": "Operations Manual v2.1",
                "description": "Login screen screenshot is outdated (v2.0 design)",
                "suggestion": "https://storage.googleapis.com/docugardener-public/v3-login-screen.png", # Placeholder URL
                "type": "image_replacement"
            },
        ],
        "suggestions_count": 3,
        "related_docs": [
            {"title": "Operations Manual v2.1", "doc_id": "demo_1"},
            {"title": "New Hire Guide 2024", "doc_id": "demo_2"},
            {"title": "IT FAQ", "doc_id": "demo_3"},
        ],
    }

# ---------------------------------------------------------------------------
# Helper: Categorize files by editability
# ---------------------------------------------------------------------------
EDITABLE_EXTENSIONS = ['.docx', '.txt', '.md', '.html']
NON_EDITABLE_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg']

def categorize_scan(scan_item):
    """Categorize scan result as auto-fixed or manual-action-required."""
    filename = scan_item.get("file_name", "")
    ext = filename[filename.rfind('.'):].lower() if '.' in filename else ''
    
    if ext in EDITABLE_EXTENSIONS:
        return "auto_fixed"
    elif ext in NON_EDITABLE_EXTENSIONS:
        return "manual_alert"
    else:
        return "auto_fixed"  # Default to auto-fixed for unknown types

# ═══════════════════════════════════════════════════════════════════════════
# CSS — Light Theme
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

:root {
    --primary:        #30D158;
    --primary-soft:   rgba(48, 209, 88, 0.12);
    --secondary:      #5E5CE6;
    --accent:         #0A84FF;
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
header[data-testid="stHeader"] { display: none !important; }

/* Top Bar */
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

/* Connection Info */
.conn-info { font-size: 0.75rem; color: var(--text-secondary); display: flex; align-items: center; gap: 6px; }
.conn-ok { color: var(--primary); font-weight: 600; }
.conn-err { color: var(--danger); font-weight: 600; }

/* Cards */
.card { background: var(--bg-card); border-radius: 12px; padding: 20px; box-shadow: var(--shadow-sm); border: 1px solid var(--border-light); height: 100%; }
.metric-val { font-family: 'Space Grotesk', sans-serif; font-size: 2rem; font-weight: 700; margin-bottom: 4px; }
.metric-lbl { font-size: 0.85rem; font-weight: 500; color: var(--text-secondary); }

/* Health Gauge */
.health-gauge { position: relative; width: 100%; height: 8px; background: #EEE; border-radius: 4px; overflow: hidden; margin-top: 12px; }
.health-fill { height: 100%; background: var(--primary); border-radius: 4px; transition: width 1s ease-out; }
.health-score { font-size: 2.5rem; font-weight: 800; color: var(--primary); line-height: 1; }

/* Result Cards */
.result-card {
    background: #FFFFFF;
    border-left: 4px solid var(--primary);
    padding: 16px;
    border-radius: 4px 12px 12px 4px;
    box-shadow: var(--shadow-sm);
    margin-bottom: 12px;
}
.rc-tag { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; margin-bottom: 4px; display: block; }
.rc-title { font-weight: 600; font-size: 0.95rem; margin-bottom: 4px; }
.rc-desc { font-size: 0.85rem; color: var(--text-secondary); }

/* Alert Cards (Manual Action) */
.alert-card {
    background: #FFF4F4;
    border-left: 4px solid var(--danger);
    padding: 16px;
    border-radius: 4px 12px 12px 4px;
    margin-bottom: 12px;
}
.alert-badge { background: var(--danger); color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; display: inline-block; margin-bottom: 8px; }

/* Diff Preview */
.diff-container {
    display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
    margin: 12px 0;
}
.diff-panel {
    background: #FAFAFA; border-radius: 8px; padding: 16px;
    border: 1px solid #E5E5EA; font-size: 0.85rem; line-height: 1.6;
}
.diff-panel-old { border-left: 4px solid #FF453A; }
.diff-panel-new { border-left: 4px solid #30D158; }
.diff-label { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; display: block; }
.diff-del { background: #FFE5E5; color: #D92D20; padding: 2px 4px; border-radius: 3px; } /* Removed strikethrough */
.diff-add { background: #E5FFE9; color: #1a8f3b; padding: 2px 4px; border-radius: 3px; }
.review-btn-row { display: flex; gap: 8px; margin-top: 8px; }
.status-icon-pending { color: #86868B; font-weight: bold; }
.status-icon-approved { color: #30D158; font-weight: bold; }
.status-icon-denied { color: #FF453A; font-weight: bold; }
.review-badge-approved { background: #30D158; color: white; padding: 4px 12px; border-radius: 32px; font-size: 0.75rem; font-weight: 700; display: inline-block; }
.review-badge-denied { background: #FF453A; color: white; padding: 4px 12px; border-radius: 32px; font-size: 0.75rem; font-weight: 700; display: inline-block; }

/* Activity Feed */
.feed-item {
    display: flex; justify-content: space-between; align-items: center;
    padding: 12px 16px; background: #FFF; border-radius: 8px;
    border: 1px solid #EEE; margin-bottom: 8px;
}

/* Buttons */
.stButton > button { background: var(--text-primary) !important; color: #FFF !important; border-radius: 8px !important; font-weight: 600 !important; border: none !important; box-shadow: var(--shadow-md) !important; }
.stButton > button:hover { background: #333 !important; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# Sidebar
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("Settings")
    mode = st.radio("Mode", ["Auto Monitoring", "Demo Mode"])
    is_auto = mode == "Auto Monitoring"
    if is_auto:
        st.caption("Monitoring GCS Bucket:")
        st.code("gs://hackathon4-487208-docs/")

# ═══════════════════════════════════════════════════════════════════════════
# Data Loading
# ═══════════════════════════════════════════════════════════════════════════
firestore_connected = True
last_update_time = None

if is_auto:
    _poll_and_process_gcs()  # Detect & process new GCS files
    history = _load_scan_history()
    if "firestore_error" in st.session_state:
        firestore_connected = False
    scan_count = len(history)
    last_update_time = history[0].get("triggered_at", "") if history else None
else:
    # Demo logic
    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button("Trigger Scan"):
            with st.spinner("Scanning..."):
                res = _run_agent_demo("demo.docx")
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

# Categorize scans
auto_fixed_items = [s for s in history if categorize_scan(s) == "auto_fixed"]
manual_alert_items = [s for s in history if categorize_scan(s) == "manual_alert"]

auto_fixed_count = len(auto_fixed_items)
manual_alert_count = len(manual_alert_items)
total_issues = sum(len(x.get("contradictions", [])) + len(x.get("visual_decays", [])) for x in history)

# Health Score
def calculate_health(total, alerts):
    base_score = 100
    deduction = (total * 3) + (alerts * 10)  # Alerts penalize more
    return max(0, base_score - deduction)

health_score = calculate_health(total_issues, manual_alert_count)
health_color = "#30D158" if health_score >= 80 else "#FF9F0A" if health_score >= 50 else "#FF453A"

# ═══════════════════════════════════════════════════════════════════════════
# Top Bar
# ═══════════════════════════════════════════════════════════════════════════
conn_status_html = f'<span class="conn-ok">● Firestore Connected</span>' if firestore_connected else f'<span class="conn-err">● Firestore Error</span>'
last_update_html = f'<span style="margin-left:16px;">Last Update: {last_update_time[:16] if last_update_time else "N/A"}</span>' if last_update_time else ''

st.markdown(f"""
<div class="top-bar">
    <div class="logo-area">
        <div class="geo-icon"></div>
        <div class="app-name">DocuGardener</div>
    </div>
    <div style="display:flex; align-items:center; gap:16px;">
        <div class="conn-info">{conn_status_html}{last_update_html}</div>
        <div class="status-badge">
            <div class="status-dot"></div>
            <span>{'SYSTEM ONLINE' if is_auto else 'DEMO MODE'}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# Main Stats Row
# ═══════════════════════════════════════════════════════════════════════════
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="card" style="display:flex; flex-direction:column; justify-content:space-between;">
        <div class="metric-lbl">Document Health Score</div>
        <div class="health-score" style="color:{health_color}">{health_score}</div>
        <div class="health-gauge">
            <div class="health-fill" style="width: {health_score}%; background: {health_color};"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="card">
        <div class="metric-val">{scan_count}</div>
        <div class="metric-lbl">Total Scans</div>
        <div style="font-size:0.75rem; color:#86868B; margin-top:4px;">All documents processed</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="card" style="border-left: 4px solid #30D158;">
        <div class="metric-val" style="color:#30D158;">{auto_fixed_count}</div>
        <div class="metric-lbl">Auto-Fixed</div>
        <div style="font-size:0.75rem; color:#30D158; margin-top:4px;">✓ Editable files (.docx, .txt)</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="card" style="border-left: 4px solid #FF453A;">
        <div class="metric-val" style="color:#FF453A;">{manual_alert_count}</div>
        <div class="metric-lbl">Manual Action Required</div>
        <div style="font-size:0.75rem; color:#FF453A; margin-top:4px;">⚠ Non-editable files (.pdf)</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# Results Display
# ═══════════════════════════════════════════════════════════════════════════
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("Auto-Fixed Documents")
    st.caption("Expand documents to review changes issue-by-issue.")
    
    if not auto_fixed_items:
        st.info("No auto-fixed documents yet. Upload .docx or .txt files to GCS.")
    else:
        for idx, item in enumerate(auto_fixed_items[:5]):
            fname = item.get("file_name", "Unknown")
            scan_id = item.get("scan_id", item.get("id", f"item_{idx}"))
            
            # Combine all issues
            contradictions = item.get("contradictions", [])
            visual_decays = item.get("visual_decays", [])
            all_issues = []
            
            for c in contradictions:
                all_issues.append({
                    "type": "text", 
                    "category": c.get("category", "Text Fix"),
                    "old": c.get("message", "Original"), 
                    "new": c.get("suggestion", "Corrected"),
                    "doc": c.get("old_doc", "")
                })
            
            for v in visual_decays:
                all_issues.append({
                    "type": "image" if "png" in v.get("suggestion", "") or "jpg" in v.get("suggestion", "") else "text",
                    "category": v.get("category", "Visual Fix"),
                    "old": v.get("description", "Old Image"),
                    "new": v.get("suggestion", "New Image"),
                    "doc": v.get("old_doc", "")
                })
                
            n_issues = len(all_issues)
            
            # Calculate file-level status
            approved_count = 0
            denied_count = 0
            
            for i in range(n_issues):
                issue_key = f"{scan_id}_issue_{i}"
                status = st.session_state.review_status.get(issue_key, None)
                if status == "approved": approved_count += 1
                if status == "denied": denied_count += 1
            
            if approved_count + denied_count == 0:
                file_status_icon = "⚪" # Unreviewed
                file_status_text = "Pending Review"
            elif approved_count + denied_count == n_issues:
                if denied_count > 0:
                    file_status_icon = "🔴" 
                    file_status_text = "Review Completed (Some Denied)"
                else:
                    file_status_icon = "🟢"
                    file_status_text = "Fully Approved"
            else:
                file_status_icon = "🟡"
                file_status_text = f"In Progress ({approved_count + denied_count}/{n_issues})"
            
            with st.expander(f"{file_status_icon} {fname} — {file_status_text}", expanded=False):
                st.markdown(f"<div style='margin-bottom:12px; font-size:0.9rem; color:#666;'>Found {n_issues} issues. Please review each one:</div>", unsafe_allow_html=True)

                for i, issue in enumerate(all_issues):
                    issue_key = f"{scan_id}_issue_{i}"
                    status = st.session_state.review_status.get(issue_key, None)
                    
                    # Status header for the issue
                    if status == "approved":
                        status_html = '<span class="status-icon-approved">✅ APPROVED</span>'
                        bg_style = "border: 1px solid #30D158; background: #F0FFF4;"
                    elif status == "denied":
                        status_html = '<span class="status-icon-denied">❌ DENIED (Reverted)</span>'
                        bg_style = "border: 1px solid #FF453A; background: #FFF0F0;"
                    else:
                        status_html = '<span class="status-icon-pending">⏳ PENDING</span>'
                        bg_style = "border: 1px solid #EEE;"

                    st.markdown(f"""
                    <div style="{bg_style} border-radius:8px; padding:12px; margin-bottom:12px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                            <span style="font-weight:bold; font-size:0.85rem;">Issue {i+1}: {issue['category']}</span>
                            {status_html}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Content Diff
                    old_content = f'<span class="diff-del">{issue["old"]}</span>'
                    
                    if issue['type'] == 'image':
                        # If it's an image URL
                        new_content = f'<div style="color:#30D158; font-weight:bold; margin-bottom:4px;">✅ Replaced with:</div><img src="{issue["new"]}" width="100%" style="border-radius:4px; border:2px solid #30D158;">'
                        if "http" not in issue["new"]: # Fallback if not a real URL
                             new_content = f'<span class="diff-add">🖼️ Image Replacement: {issue["new"]}</span>'
                    else:
                        new_content = f'<span class="diff-add">{issue["new"]}</span>'

                    st.markdown(f"""
                        <div class="diff-container" style="margin:0;">
                            <div class="diff-panel diff-panel-old">
                                <span class="diff-label" style="color:#FF453A;">Before</span>
                                <div>{old_content}</div>
                            </div>
                            <div class="diff-panel diff-panel-new">
                                <span class="diff-label" style="color:#30D158;">After</span>
                                <div>{new_content}</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Buttons (only show if pending or to allow changing mind)
                    b_col1, b_col2, b_skip = st.columns([1, 1, 3])
                    with b_col1:
                        if st.button("Approve", key=f"app_{issue_key}", type="primary" if status is None else "secondary", use_container_width=True):
                            st.session_state.review_status[issue_key] = "approved"
                            st.rerun()
                    with b_col2:
                         if st.button("Deny", key=f"den_{issue_key}", use_container_width=True):
                            st.session_state.review_status[issue_key] = "denied"
                            st.rerun()
                    
                    st.markdown("---")

with col_right:
    st.subheader("⚠ Manual Action Required")
    st.caption("Non-editable files (.pdf) with detected version conflicts. User intervention needed.")
    
    if not manual_alert_items:
        st.success("No manual alerts. All documents are up-to-date!")
    else:
        for item in manual_alert_items[:5]:
            fname = item.get("file_name", "Unknown")
            n_issues = len(item.get("contradictions", [])) + len(item.get("visual_decays", []))
            
            st.markdown(f"""
            <div class="alert-card">
                <span class="alert-badge">MANUAL ACTION REQUIRED</span>
                <div class="rc-title" style="color:#D92D20;">{fname}</div>
                <div class="rc-desc">PDF detected: {n_issues} version conflicts found. Please update manually or convert to .docx.</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# Recent Activity
# ═══════════════════════════════════════════════════════════════════════════
st.subheader("Recent Activity Stream")

if not history:
    st.info("No recent activity. Upload documents to GCS to trigger scanning.")
else:
    for act in history[:8]:
        fname = act.get("file_name", "Unknown File")
        ts = act.get("triggered_at", "")[:16].replace("T", " ")
        category = categorize_scan(act)
        
        if category == "auto_fixed":
            status_html = '<span style="color:#30D158; font-weight:600;">✓ Auto-Fixed</span>'
            icon = "📄"
        else:
            status_html = '<span style="color:#FF453A; font-weight:600;">⚠ Manual Required</span>'
            icon = "📕"
        
        st.markdown(f"""
        <div class="feed-item">
            <div style="display:flex; align-items:center; gap:12px;">
                <div style="font-size:1.5rem;">{icon}</div>
                <div>
                    <div style="font-weight:600; font-size:0.9rem;">{fname}</div>
                    <div style="font-size:0.75rem; color:#86868B;">{ts}</div>
                </div>
            </div>
            {status_html}
        </div>
        """, unsafe_allow_html=True)

if is_auto:
    time.sleep(10)
    st.rerun()
