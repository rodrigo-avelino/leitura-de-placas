import streamlit as st
from datetime import datetime
from src.controllers.placaController import PlacaController
from src.components.pdiPanel import painel_pdi      # novo componente
from src.components.etapasPDI import mostrar_etapas  # mantém para compatibilidade / debug :contentReference[oaicite:3]{index=3}

def app():
    st.title("🔍 Processar Imagem")

    # Data e Hora
    st.subheader("📅 Data e Hora da Captura")
    c1, c2 = st.columns(2)
    with c1:
        data_captura = st.date_input("Data", value=datetime.today())
    with c2:
        hora_captura = st.time_input("Hora", value=datetime.now().time())

    # Upload
    st.subheader("📤 Upload de Imagens")
    uploaded_files = st.file_uploader(
        "Clique para selecionar imagens ou arraste aqui",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    # CTA
    processar = st.button("🚀 Processar", type="primary")

    if processar:
        if not uploaded_files:
            st.warning("Envie ao menos 1 imagem para processar.")
            return

        for file in uploaded_files:
            with st.status(f"Processando **{file.name}**…", expanded=True) as status:
                dt_captura = datetime.combine(data_captura, hora_captura)
                # seu controller faz todo o pipeline e retorna o dict com as imagens de cada etapa
                result = PlacaController.processarImagem(file.name, dt_captura)  # ajuste no controller p/ aceitar data

                # Painel PDI com “crops” por etapa
                painel_pdi(result)  # exibe os cards por etapa com o resultado de cada uma

                # (Opcional) manter a visualização antiga para validação rápida
                # mostrar_etapas(result)  # usa sua função atual de exibir imagens por chave :contentReference[oaicite:4]{index=4}

                status.update(label=f"✅ {file.name} finalizado", state="complete")

        st.success("Processamento concluído!")
