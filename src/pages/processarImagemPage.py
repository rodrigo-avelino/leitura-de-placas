import streamlit as st
from datetime import datetime
from src.controllers.placaController import PlacaController
from src.components.pdiPanel import panelPDI

class ProcessarImagemPage:

    def app():
        st.title("Processar Imagem")

        # Data e hora
        st.subheader("Data e Hora da Captura")
        c1, c2 = st.columns(2)
        with c1:
            data_captura = st.date_input("Data", value=datetime.today())
        with c2:
            hora_captura = st.time_input("Hora", value=datetime.now().time())

        # Upload
        st.subheader("Upload de Imagens")
        uploaded_file = st.file_uploader(
            "Selecione imagens ou arraste para cá",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=False,
        )

        # Estado do painel
        if "pdi_result" not in st.session_state:
            st.session_state["pdi_result"] = {}

        # Painel sempre visível
        panel_placeholder = st.empty()
        with panel_placeholder.container():
            panelPDI(st.session_state["pdi_result"])

        # Botão
        if st.button("Processar", type="primary", use_container_width=True):
            if not uploaded_file:
                st.warning("Envie ao menos 1 imagem para processar.")
                return

            file = uploaded_file  # apenas um arquivo
            st.session_state["pdi_result"] = {}
            with panel_placeholder.container():
                panelPDI(st.session_state["pdi_result"])

            def on_update(delta: dict):
                st.session_state["pdi_result"].update(delta)
                with panel_placeholder.container():
                    panelPDI(st.session_state["pdi_result"])

            with st.status(f"Processando {file.name}…", expanded=True) as status:
                dt_captura = datetime.combine(data_captura, hora_captura)
                result = PlacaController.processarImagem(file, dt_captura, on_update=on_update)
                st.session_state["pdi_result"].update(result.get("panel", {}))

                with panel_placeholder.container():
                    panelPDI(st.session_state["pdi_result"])

                placa = result.get("texto_final")
                if placa:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.success(f"Placa reconhecida: {placa}")
                    with col2:
                        st.image(result['etapas']['recorte'], width='stretch')

                    status.update(label=f"{file.name} finalizado (OK: {placa})", state="complete")
                else:
                    st.warning("Não foi possível validar a placa.")
                    status.update(label=f"{file.name} finalizado (sem validação)", state="complete")