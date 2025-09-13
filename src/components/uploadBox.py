import streamlit as st

def upload_box():
    st.subheader("📤 Upload de Imagens")
    return st.file_uploader(
        "Clique para selecionar imagens ou arraste aqui",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )
