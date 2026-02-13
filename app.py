import streamlit as st
from views.admin_view import render_admin_dashboard
from views.user_view import render_user_drive

# Page Configuration (Must be first)
st.set_page_config(
    page_title="DocuGardener",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar for Role Switching
with st.sidebar:
    st.markdown("## 👤 View Mode")
    role = st.radio(
        "Select Role:",
        ["Admin Dashboard", "End User Drive"],
        index=0,
        label_visibility="collapsed"
    )
    st.caption("Switch between Administrator (AI Review) and End User (File Management) views.")
    st.divider()

# Dispatch
if role == "Admin Dashboard":
    render_admin_dashboard()
else:
    render_user_drive()
