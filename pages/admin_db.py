import streamlit as st
import os

DB_PATH = "wc2026.db"

st.title("🔧 Admin - Database Manager")

password = st.text_input("Admin password", type="password")
if password != "admin123":
    st.stop()

# --- DOWNLOAD ---
st.subheader("⬇️ Download current DB")
if os.path.exists(DB_PATH):
    with open(DB_PATH, "rb") as f:
        data = f.read()
    st.write(f"File size: **{len(data):,} bytes**")  # confirm it's the live file
    st.download_button("Download wc2026.db", data, "wc2026.db", "application/octet-stream")
else:
    st.error(f"DB not found at: {os.path.abspath(DB_PATH)}")

# --- UPLOAD ---
st.subheader("⬆️ Upload updated DB")
uploaded = st.file_uploader("Upload your edited .db file", type=["db"])
if uploaded:
    with open(DB_PATH, "wb") as f:
        f.write(uploaded.read())
    st.success("✅ Database replaced! Changes are live.")
    st.rerun()
