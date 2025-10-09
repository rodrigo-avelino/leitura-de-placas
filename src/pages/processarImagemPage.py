import streamlit as st
from datetime import datetime, time, date
from src.controllers.placaController import PlacaController
from src.components.pdiPanel import panelPDI

class ProcessarImagemPage:

    def app():
        # -----------------------------------------------
        # Título da página
        # -----------------------------------------------
        st.title("Processar Imagem")

        # -----------------------------------------------
        # Seção de captura de data/hora
        # O usuário informa quando a imagem foi capturada.
        # Isso será salvo junto ao registro no banco.
        # -----------------------------------------------
        st.subheader("Data e Hora da Captura")

        # Layout: dois campos lado a lado (data | hora)
        c1, c2 = st.columns(2)

        with c1:
            # Data padrão = hoje; limite mínimo 01/01/2000, máximo hoje
            hoje = datetime.today().date()
            data_captura = st.date_input(
                "Data",
                value=hoje,
                max_value=hoje,
                min_value=date(2000, 1, 1),
                format="DD/MM/YYYY"
            )

        with c2:
            # -------------------------------------------
            # substitui o dropdown por timeinput
            # permite o usuário escolher qualquer hora/minuto
            # valor padrao = hora atual 
            # -------------------------------------------
            agora = datetime.now().time()
            hora_captura = st.time_input(
                "Hora",
                value=time(agora.hour, agora.minute)
            )

        # -----------------------------------------------
        # Upload de imagem (apenas 1 arquivo)
        # -----------------------------------------------
        st.subheader("Upload de Imagens")
        uploaded_file = st.file_uploader(
            "Selecione imagens ou arraste para cá",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=False,
        )

        # -----------------------------------------------
        # Estado compartilhado do painel de PDI (etapas)
        # Mantém o resultado entre interações para renderizar
        # as imagens parciais (original, bordas, recorte etc.)
        # -----------------------------------------------
        if "pdi_result" not in st.session_state:
            st.session_state["pdi_result"] = {}

        # Placeholder onde o painel será desenhado
        panel_placeholder = st.empty()
        with panel_placeholder.container():
            # Renderiza o painel com o estado atual (inicialmente vazio)
            panelPDI(st.session_state["pdi_result"])

        # -----------------------------------------------
        # Botão de processamento
        # Ao clicar:
        #  - valida se há arquivo
        #  - zera o painel
        #  - define on_update() para atualizações em tempo real
        #  - chama o controller para processar a imagem
        #  - mostra status e resultado (placa/crop) ao final
        # -----------------------------------------------
        if st.button("Processar", type="primary", width='stretch',):
            if not uploaded_file:
                st.warning("Envie ao menos 1 imagem para processar.")
                return

            file = uploaded_file  # apenas um arquivo
            # Reseta o painel antes de iniciar o processamento
            st.session_state["pdi_result"] = {}
            with panel_placeholder.container():
                panelPDI(st.session_state["pdi_result"])

            # ---------------------------------------------------
            # Callback usado pelo controller para empurrar imagens
            # intermediárias (original, contornos, recorte etc.)
            # enquanto o pipeline executa. A UI re-renderiza o
            # painel a cada atualização para efeito "tempo real".
            # ---------------------------------------------------
            def on_update(delta: dict):
                st.session_state["pdi_result"].update(delta)
                with panel_placeholder.container():
                    panelPDI(st.session_state["pdi_result"])

            # ---------------------------------------------------
            # Faixa de status visual durante o processamento.
            # ---------------------------------------------------
            with st.status(f"Processando {file.name}…", expanded=True) as status:
                # Constrói o datetime final a partir dos widgets
                dt_captura = datetime.combine(data_captura, hora_captura)

                # Dispara o pipeline no controller:
                # 1) Pré-processamento
                # 2) Bordas, contornos e filtro
                # 3) Recorte e binarização
                # 4) Segmentação + OCR
                # 5) Montagem + Validação
                # 6) Persistência (salva no banco)
                result = PlacaController.processarImagem(file, dt_captura, on_update=on_update)

                # Garante que o painel tenha tudo que o controller reportou
                st.session_state["pdi_result"].update(result.get("panel", {}))
                with panel_placeholder.container():
                    panelPDI(st.session_state["pdi_result"])

                # Exibe o desfecho do reconhecimento
                placa = result.get("texto_final")
                if placa:
                    # Mostra mensagem de sucesso e o recorte da placa detectada
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.success(f"Placa reconhecida: {placa}")
                    with col2:
                        # Thumbnail do recorte da placa
                        st.image(result['etapas']['recorte'], width='stretch')

                    # Atualiza a barra de status (sucesso)
                    status.update(label=f"{file.name} finalizado (OK: {placa})", state="complete")
                else:
                    # Sem validação final (OCR falhou ou não passou na regra)
                    st.warning("Não foi possível validar a placa.")
                    status.update(label=f"{file.name} finalizado (sem validação)", state="complete")
