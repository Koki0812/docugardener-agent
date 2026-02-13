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
    </style>
    """, unsafe_allow_html=True)

    if "current_path" not in st.session_state:
        st.session_state["current_path"] = ""

    current_path = st.session_state["current_path"]

    # Header
    st.markdown('<div class="drive-header">📂 My Drive</div>', unsafe_allow_html=True)

    # GCS Client
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET)
    except Exception as e:
        st.error(f"Failed to connect to GCS: {e}")
        return

    # Breadcrumbs & Navigation
    col_nav, col_action = st.columns([3, 1])
    with col_nav:
        if current_path:
            if st.button("⬅ Back", key="nav_back"):
                # Go up one level
                if "/" in current_path.rstrip("/"):
                    parent = current_path.rstrip("/").rsplit("/", 2)[0] + "/"
                    if parent == "/": parent = ""
                    # Actually rsuffix logic is tricky. 
                    # "foo/bar/" -> rstrip -> "foo/bar" -> rsplit -> ["foo", "bar"] -> parent "foo/"
                    parts = current_path.rstrip("/").split("/")
                    if len(parts) > 1:
                        st.session_state["current_path"] = "/".join(parts[:-1]) + "/"
                    else:
                        st.session_state["current_path"] = ""
                else:
                    st.session_state["current_path"] = ""
                st.rerun()
            st.caption(f"Location: Home / {current_path}")
        else:
            st.caption("Location: Home /")

    with col_action:
        with st.popover("➕ New Folder"):
            new_folder_name = st.text_input("Folder Name")
            if st.button("Create"):
                if new_folder_name:
                    clean_name = new_folder_name.strip().replace("/", "_")
                    blob = bucket.blob(f"{current_path}{clean_name}/")
                    blob.upload_from_string("")
                    st.toast(f"Folder '{clean_name}' created!")
                    st.rerun()

    st.markdown("---")

    # List Blobs
    # Note: listing with delimiter populates prefixes
    blobs_iter = bucket.list_blobs(prefix=current_path, delimiter="/")
    files = list(blobs_iter) # Consume iterator
    folders = list(blobs_iter.prefixes) # Now prefixes is populated

    # Display Folders
    if folders:
        st.subheader("Folders")
        cols = st.columns(4)
        for i, folder in enumerate(folders):
            # folder is full prefix e.g. "path/to/folder/"
            # we want display name "folder"
            folder_name = folder.rstrip("/").split("/")[-1]
            with cols[i % 4]:
                if st.button(f"📁 {folder_name}", key=f"folder_{folder}"):
                    st.session_state["current_path"] = folder
                    st.rerun()

    # Display Files
    st.subheader("Files")
    
    # Upload Zone
    uploaded_file = st.file_uploader("Upload File", label_visibility="collapsed")
    if uploaded_file:
        # Check if already uploaded in this session to avoid loop?
        # Streamlit file uploader preserves state.
        # We need to perform action and then maybe clear? 
        # Or just upload.
        blob_path = f"{current_path}{uploaded_file.name}"
        blob = bucket.blob(blob_path)
        # Check exists?
        if not blob.exists():
            blob.upload_from_string(uploaded_file.getvalue(), content_type=uploaded_file.type)
            st.toast(f"Uploaded {uploaded_file.name}")
            time.sleep(1) # Wait for consistency
            st.rerun()

    if not files and not folders:
        st.info("This folder is empty.")

    for file in files:
        name = file.name.replace(current_path, "")
        if not name: continue # Skip the placeholder itself
        if name.endswith("/"): continue 

        with st.container():
            c1, c2, c3 = st.columns([0.05, 0.7, 0.25])
            with c1:
                st.write("📄")
            with c2:
                st.write(name)
            with c3:
                # 2-step Download Logic
                dl_key = f"dl_ready_{file.name}"
                if dl_key not in st.session_state:
                    if st.button("Download", key=f"btn_load_{file.name}"):
                        st.session_state[dl_key] = file.download_as_bytes()
                        st.rerun()
                else:
                    c_dl, c_cancel = st.columns([1, 1])
                    with c_dl:
                        st.download_button(
                            label="Save",
                            data=st.session_state[dl_key],
                            file_name=name,
                            mime=file.content_type,
                            key=f"btn_save_{file.name}"
                        )
                    with c_cancel:
                        if st.button("X", key=f"btn_cancel_{file.name}"):
                            del st.session_state[dl_key]
                            st.rerun()
            st.divider()
