import streamlit as st
from datetime import datetime

# --- FUNÇÃO DE CALLBACK PARA EXCLUSÃO ---
def set_delete_id(record_id):
    """Define o ID do registro a ser excluído no session_state."""
    st.session_state.delete_id = record_id

def registroTable(registros):
    """
    Renderiza uma tabela simples de registros de placas no Streamlit,
    incluindo as ações de Visualizar e Excluir.
    """

    if not registros:
        return

    # ---- Título com contador de resultados ----
    st.markdown(
        f"<h3>Consulta de Placas <span style='color:#69a6ff'>({len(registros)})</span></h3>",
        unsafe_allow_html=True
    )

    # ---- CSS inline para estilizar linhas/cabeçalhos/células e detalhes ----
    st.markdown("""
        <style>
        .row-sep {
            border-bottom: 1px solid #2a2f3a;
            margin: 6px 0 10px 0;
        }
        .header {
            color: #c9d1d9;
            font-weight: 700;
            padding: 6px 0 2px 0;
        }
        .cell-placa {
            font-weight: 800;
            letter-spacing: 1px;
            color: #69a6ff;
        }
        .cell-data {
            color: #9aa4b2;
        }
        /* CSS para os detalhes dentro do expander */
        .detail-label {
            color: #9aa4b2;
            font-size: 0.85em;
            margin-bottom: 0;
        }
        .detail-value {
            color: #ffffff;
            font-weight: 600;
            font-size: 1.1em;
            margin-top: 0;
            margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    # ---- Cabeçalho da "tabela" ----
    # 2.2 (Placa), 1.5 (Hora), 1.3 (Data), 1.4 (Ações)
    c1, c2, c3, c4 = st.columns([2.2, 1.5, 1.3, 1.4])
    with c1: st.markdown("<div class='header'>Placa</div>", unsafe_allow_html=True)
    with c2: st.markdown("<div class='header'>Hora</div>", unsafe_allow_html=True)
    with c3: st.markdown("<div class='header'>Data</div>", unsafe_allow_html=True)
    with c4: st.markdown("<div class='header'>Ações</div>", unsafe_allow_html=True) 
    st.markdown("<div class='row-sep'></div>", unsafe_allow_html=True)

    # ---- Itera registros e monta cada linha ----
    for i, r in enumerate(registros):
        registro_id = r.get("id") 
        placa = r["placa"]
        data  = r["data"]
        img   = r.get("imagem")

        # Tenta converter e formatar data/hora
        hora_fmt, data_fmt = "", ""
        try:
            dt = datetime.strptime(data, "%Y-%m-%d %H:%M:%S")
            hora_fmt = dt.strftime("%H:%M:%S") # Adicionado segundos para mais detalhe
            data_fmt = dt.strftime("%d/%m/%Y")
        except Exception:
            data_fmt = data

        # Cria estado expandido/fechado por linha (toggle)
        st.session_state.setdefault(f"open_{i}", False)

        # Linha com 4 colunas alinhadas verticalmente ao centro.
        col1, col2, col3, col4 = st.columns([2.2, 1.5, 1.3, 1.4], vertical_alignment="center")
        with col1:
            st.markdown(f"<div class='cell-placa'>{placa}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='cell-data'>{hora_fmt}</div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='cell-data'>{data_fmt}</div>", unsafe_allow_html=True)

        # Coluna de Ações com dois botões
        with col4:
            b_ver, b_del = st.columns([1, 1])

            with b_ver:
                # Botão "Ver"
                if st.button("Ver", key=f"toggle_{i}", width='stretch', help="Clique para visualizar o crop da placa."): 
                    st.session_state[f"open_{i}"] = not st.session_state[f"open_{i}"]
            
            with b_del:
                if registro_id is not None:
                    if st.button("🗑️", 
                                 key=f"delete_{registro_id}", 
                                 on_click=set_delete_id, 
                                 args=[registro_id], 
                                 width='stretch',
                                 help="Excluir permanentemente este registro."
                                 ): 
                        pass
                else:
                    st.markdown("—")


        # Área expandida: exibe imagem (crop da placa) e detalhes
        if st.session_state[f"open_{i}"]:
            with st.expander(f"Visualizando imagem de {placa}", expanded=True):
                
                # Divide o expander em 2 colunas: 1 para imagem, 1 para detalhes
                # Proporção ajustada para acomodar imagem maior e texto
                col_img, col_info = st.columns([2, 2.5]) 
                
                with col_img:
                    if img:
                        # Exibição da imagem com largura aumentada para melhor visualização (e para forçar a altura)
                        st.image(img, caption=f"Crop da placa {placa}", width=500)
                    else:
                        st.info("Nenhuma imagem disponível.")
                
                with col_info:
                    # Informações Detalhadas
                    
                    # Placa
                    st.markdown("<p class='detail-label'>PLACA IDENTIFICADA</p>", unsafe_allow_html=True)
                    st.markdown(f"<p class='detail-value'>{placa}</p>", unsafe_allow_html=True)
                    
                    # Dia/Data
                    st.markdown("<p class='detail-label'>DATA DE REGISTRO</p>", unsafe_allow_html=True)
                    st.markdown(f"<p class='detail-value'>{data_fmt}</p>", unsafe_allow_html=True)
                    
                    # Hora
                    st.markdown("<p class='detail-label'>HORA EXATA</p>", unsafe_allow_html=True)
                    st.markdown(f"<p class='detail-value'>{hora_fmt}</p>", unsafe_allow_html=True)


        # Separador visual entre linhas.
        st.markdown("<div class='row-sep'></div>", unsafe_allow_html=True)