import streamlit as st
from src.components.uploadBox import upload_box
from src.components.etapasPDI import mostrar_etapas
from src.controllers.placaController import PlacaController
from src.config.db import UPLOAD_DIR  # <- garantir esse import

def app():
    st.title("🔍 Processar Imagem")

    uploaded_files = upload_box()

    if uploaded_files:
        for file in uploaded_files:
            # 1) salvar no disco onde o controller procura
            save_path = UPLOAD_DIR / file.name

            file.seek(0)
            data = file.getvalue()  # bytes do arquivo
            with open(save_path, "wb") as f:
                f.write(data)

            # sanity check (evita _src.empty())
            if (not save_path.exists()) or save_path.stat().st_size == 0:
                st.error(f"Falha ao salvar '{file.name}' em {save_path}.")
                continue

            # 2) processar pelo nome (como já estava)
            with st.spinner(f"Processando {file.name}..."):
                result = PlacaController.processarImagem(file.name)

            # 3) exibir etapas/resultado
            mostrar_etapas(result)

        if st.button("🚀 Processar", type="primary"):
            st.success("Processamento concluído!")
