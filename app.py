import streamlit as st
from services.logging_service import setup_logging
from views.admin_view import render_admin_dashboard
from views.user_view import render_user_drive

# Initialize logging (must be before any other operations)
setup_logging()

# Page Configuration (Must be first)
st.set_page_config(
    page_title="DocuAlign AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar for Role Switching
with st.sidebar:
    st.markdown("## 👤 表示モード")
    role = st.radio(
        "ロールを選択:",
        ["管理者ダッシュボード", "エンドユーザー ドライブ"],
        index=0,
        label_visibility="collapsed"
    )
    st.caption("管理者 (AI レビュー) と エンドユーザー (ファイル管理) を切り替えます。")
    st.divider()

# Dispatch
if role == "管理者ダッシュボード":
    render_admin_dashboard()
else:
    render_user_drive()
