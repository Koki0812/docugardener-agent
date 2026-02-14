import streamlit as st
from google.cloud import storage
from config.settings import GCS_BUCKET
import io
import time

def render_user_drive():
    st.markdown("""
    <style>
    .drive-header { font-family: 'Space Grotesk', sans-serif; font-size: 1.5rem; font-weight: 700; margin-bottom: 1rem; }
    .folder-item { 
        padding: 10px; border-radius: 8px; cursor: pointer; 
        background: #F5F5F7; margin-bottom: 8px; display: flex; align-items: center; gap: 8px;
        transition: background 0.2s;
    }
    .folder-item:hover { background: #E5E5EA; }
    .file-item {
        padding: 10px; border-radius: 8px; border: 1px solid #EEE;
        background: #FFF; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;
    }
    .file-icon { font-size: 1.2rem; }
    .file-name { font-weight: 500; font-size: 0.9rem; }
    .ai-badge {
        display: inline-flex; align-items: center; gap: 4px;
        background: linear-gradient(135deg, #E8F5E9, #C8E6C9); color: #2E7D32;
        font-size: 0.7rem; font-weight: 700; padding: 3px 8px;
        border-radius: 12px; border: 1px solid #A5D6A7;
        white-space: nowrap;
    }
    .file-row-modified {
        border-left: 3px solid #30D158 !important;
        background: #F0FFF4 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if "current_path" not in st.session_state:
        st.session_state["current_path"] = ""

    current_path = st.session_state["current_path"]

    # Load AI-modified file names from Firestore scan history
    ai_modified_files = set()
    try:
        from services.firestore_service import get_latest_results
        scan_results = get_latest_results(limit=50)
        for scan in scan_results:
            fname = scan.get("file_name", "")
            if fname:
                ai_modified_files.add(fname)
    except Exception:
        pass  # Firestore unavailable — skip badge display

    # Header
    st.markdown('<div class="drive-header">📂 マイドライブ</div>', unsafe_allow_html=True)

    # GCS Client
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET)
    except Exception as e:
        st.error(f"GCS接続エラー: {e}")
        return

    # Breadcrumbs & Navigation
    col_nav, col_action = st.columns([3, 1])
    with col_nav:
        if current_path:
            if st.button("⬅ 戻る", key="nav_back"):
                parts = current_path.rstrip("/").split("/")
                if len(parts) > 1:
                    st.session_state["current_path"] = "/".join(parts[:-1]) + "/"
                else:
                    st.session_state["current_path"] = ""
                st.rerun()
            st.caption(f"場所: ホーム / {current_path}")
        else:
            st.caption("場所: ホーム /")

    with col_action:
        with st.popover("➕ 新規フォルダ"):
            new_folder_name = st.text_input("フォルダ名")
            if st.button("作成"):
                if new_folder_name:
                    clean_name = new_folder_name.strip().replace("/", "_")
                    blob = bucket.blob(f"{current_path}{clean_name}/")
                    blob.upload_from_string("")
                    st.toast(f"フォルダ「{clean_name}」を作成しました")
                    st.rerun()

    st.markdown("---")

    # List Blobs
    blobs_iter = bucket.list_blobs(prefix=current_path, delimiter="/")
    files = list(blobs_iter)
    folders = list(blobs_iter.prefixes)

    # Display Folders
    if folders:
        st.subheader("フォルダ")
        cols = st.columns(4)
        for i, folder in enumerate(folders):
            folder_name = folder.rstrip("/").split("/")[-1]
            with cols[i % 4]:
                if st.button(f"📁 {folder_name}", key=f"folder_{folder}"):
                    st.session_state["current_path"] = folder
                    st.rerun()

    # Display Files
    st.subheader("ファイル")
    
    # Upload Zone
    uploaded_file = st.file_uploader("ファイルアップロード", label_visibility="collapsed")
    if uploaded_file:
        blob_path = f"{current_path}{uploaded_file.name}"
        blob = bucket.blob(blob_path)
        if not blob.exists():
            blob.upload_from_string(uploaded_file.getvalue(), content_type=uploaded_file.type)
            st.toast(f"「{uploaded_file.name}」をアップロードしました")
            time.sleep(1)
            st.rerun()

    if not files and not folders:
        st.info("このフォルダは空です。")

    for file in files:
        name = file.name.replace(current_path, "")
        if not name: continue
        if name.endswith("/"): continue

        is_ai_modified = file.name in ai_modified_files

        with st.container():
            if is_ai_modified:
                st.markdown('<div class="file-row-modified" style="padding:8px 12px; border-radius:8px; margin-bottom:4px;">', unsafe_allow_html=True)

            c1, c2, c3 = st.columns([0.05, 0.7, 0.25])
            with c1:
                st.write("📄")
            with c2:
                if is_ai_modified:
                    st.markdown(f'{name} <span class="ai-badge">🤖 AI修正済</span>', unsafe_allow_html=True)
                else:
                    st.write(name)
            with c3:
                dl_key = f"dl_ready_{file.name}"
                if dl_key not in st.session_state:
                    if st.button("ダウンロード", key=f"btn_load_{file.name}"):
                        st.session_state[dl_key] = file.download_as_bytes()
                        st.rerun()
                else:
                    c_dl, c_cancel = st.columns([1, 1])
                    with c_dl:
                        st.download_button(
                            label="保存",
                            data=st.session_state[dl_key],
                            file_name=name,
                            mime=file.content_type,
                            key=f"btn_save_{file.name}"
                        )
                    with c_cancel:
                        if st.button("✕", key=f"btn_cancel_{file.name}"):
                            del st.session_state[dl_key]
                            st.rerun()

            if is_ai_modified:
                st.markdown('</div>', unsafe_allow_html=True)
            st.divider()
