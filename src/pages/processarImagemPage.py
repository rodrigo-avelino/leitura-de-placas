import streamlit as st
from src.components.uploadBox import upload_box
from src.components.etapasPDI import mostrar_etapas
from src.controllers.placaController import PlacaController

def app():
    st.title("🔍 Processar Imagem")

    uploaded_files = upload_box()

    if uploaded_files:
        for file in uploaded_files:
            with st.spinner(f"Processando {file.name}..."):
                result = PlacaController.processarImagem(file.name)

                mostrar_etapas(result)

        if st.button("🚀 Processar", type="primary"):
            st.success("Processamento concluído!")
