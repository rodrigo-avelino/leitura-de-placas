import streamlit as st
from datetime import datetime, time, date
from src.controllers.placaController import PlacaController
from src.components.pdiPanel import panelPDI

class ProcessarImagemPage:

    def app():
        # -----------------------------------------------
        # Título da página
        # -----------------------------------------------
        st.title("PROCESSAR IMAGEM")

        # -----------------------------------------------
        # Seção de captura de data/hora
        # -----------------------------------------------
        st.subheader("Data e Hora da Captura")

        # Pega a hora atual para definir os valores iniciais
        agora = datetime.now()
        
        # ----------------------------------------------------------------------------------
        # LAYOUT JUSTIFICADO À ESQUERDA: Apenas três colunas (Data | Hora | Minuto)
        # O alinhamento padrão do Streamlit forçará o conteúdo à esquerda
        # [2] para Data, [1] para Hora, [1] para Minuto
        # ----------------------------------------------------------------------------------
        c1, c2, c3 = st.columns([2, 1, 1])

        with c1:
            # Data padrão = hoje...
            hoje = datetime.today().date()
            data_captura = st.date_input(
                "Data",
                value=hoje,
                max_value=hoje,
                min_value=date(2000, 1, 1),
                format="DD/MM/YYYY"
            )

        with c2:
            # Seleção de Hora com Select Box (Dropdown)
            horas_opcoes = [f"{i:02d}" for i in range(24)]
            hora_selecionada = st.selectbox(
                "Hora",
                options=horas_opcoes,
                index=horas_opcoes.index(f"{agora.hour:02d}")
            )

        with c3:
            # Seleção de Minuto com Select Box (Dropdown)
            minutos_opcoes = [f"{i:02d}" for i in range(60)]
            minuto_selecionado = st.selectbox(
                "Minuto",
                options=minutos_opcoes,
                index=minutos_opcoes.index(f"{agora.minute:02d}")
            )

        # Converte as strings selecionadas para um objeto time Python
        hora_captura = time(int(hora_selecionada), int(minuto_selecionado))
        # -----------------------------------------------------


        # -----------------------------------------------
        # Upload de imagem (já alinhado à esquerda)
        # -----------------------------------------------
        st.subheader("Upload de Imagens")
        uploaded_file = st.file_uploader(
            "Selecione imagens ou arraste para cá",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=False,
        )

        # -----------------------------------------------
        # Estado compartilhado do painel de PDI (etapas)
        # -----------------------------------------------
        if "pdi_result" not in st.session_state:
            st.session_state["pdi_result"] = {}

        # Placeholder onde o painel será desenhado
        panel_placeholder = st.empty()
        with panel_placeholder.container():
            panelPDI(st.session_state["pdi_result"])

        # -----------------------------------------------
        # Botão de processamento
        # -----------------------------------------------
        if st.button("Processar", type="primary", width='stretch',):
            if not uploaded_file:
                st.warning("Envie ao menos 1 imagem para processar.")
                return

            file = uploaded_file 
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