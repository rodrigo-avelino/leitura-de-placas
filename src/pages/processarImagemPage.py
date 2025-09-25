import streamlit as st
from datetime import datetime, time, date
from src.controllers.placaController import PlacaController
from src.components.pdiPanel import panelPDI

class ProcessarImagemPage:

    def app():
        st.title("Processar Imagem")

        st.subheader("Data e Hora da Captura")

        c1, c2 = st.columns(2)

        with c1:
            hoje = datetime.today().date()
            data_captura = st.date_input(
                "Data",
                value=hoje,
                max_value=hoje,
                min_value=date(2000, 1, 1),
                format="DD/MM/YYYY"
            )

        with c2:
            # gerar opções no formato brasileiro (24h, de meia em meia hora)
            opcoes = []
            valores = {}
            for h in range(24):
                for m in (0, 30):
                    t = time(h, m)
                    label = f"{h:02d}:{m:02d}"  # ex: 07:00, 07:30
                    opcoes.append(label)
                    valores[label] = t

            # seleciona o horário atual arredondado para a meia hora mais próxima
            agora = datetime.now()
            minuto_ajustado = 0 if agora.minute < 30 else 30
            hora_atual_label = f"{agora.hour:02d}:{minuto_ajustado:02d}"

            hora_str = st.selectbox("Hora", opcoes, index=opcoes.index(hora_atual_label))
            hora_captura = valores[hora_str]

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
        if st.button("Processar", type="primary", width='stretch',):
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