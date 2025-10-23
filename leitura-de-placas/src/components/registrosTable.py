import streamlit as st
from datetime import datetime

def registroTable(registros):
    """
    Renderiza uma tabela simples de registros de placas no Streamlit,
    exibindo placa, hora, data e um botão para visualizar a imagem (crop).

    Parâmetros
    ----------
    registros : list[dict]
        Cada item deve conter ao menos:
          - "placa": str
          - "data": str (timestamp no formato "%Y-%m-%d %H:%M:%S" ou similar)
        Opcional:
          - "imagem": caminho/array/bytes aceitos por st.image
    """

    # ---- Título com contador de resultados ----
    st.markdown(
        f"<h3>Consulta de Placas <span style='color:#69a6ff'>({len(registros)})</span></h3>",
        unsafe_allow_html=True
    )

    # ---- CSS inline para estilizar linhas/cabeçalhos/células ----
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
        </style>
    """, unsafe_allow_html=True)

    # ---- Cabeçalho da "tabela" usando 4 colunas ----
    c1, c2, c3, c4 = st.columns([2.2, 1.5, 1.3, 1.0])
    with c1: st.markdown("<div class='header'>Placa</div>", unsafe_allow_html=True)
    with c2: st.markdown("<div class='header'>Hora</div>", unsafe_allow_html=True)
    with c3: st.markdown("<div class='header'>Data</div>", unsafe_allow_html=True)
    with c4: st.markdown("<div class='header'>Visualizar</div>", unsafe_allow_html=True)
    st.markdown("<div class='row-sep'></div>", unsafe_allow_html=True)

    # ---- Itera registros e monta cada linha ----
    for i, r in enumerate(registros):
        placa = r["placa"]
        data  = r["data"]
        img   = r.get("imagem")

        # Tenta converter a string 'data' para datetime no padrão ISO
        # e formatar nos padrões pt-BR (hora 24h e data dd/mm/yyyy).
        hora_fmt, data_fmt = "", ""
        try:
            dt = datetime.strptime(data, "%Y-%m-%d %H:%M:%S")
            hora_fmt = dt.strftime("%H:%M")
            data_fmt = dt.strftime("%d/%m/%Y")
        except Exception:
            # Se falhar a conversão, mostra o valor original de 'data'.
            data_fmt = data

        # Cria estado expandido/fechado por linha (toggle) apenas uma vez.
        st.session_state.setdefault(f"open_{i}", False)

        # Linha com 4 colunas alinhadas verticalmente ao centro.
        col1, col2, col3, col4 = st.columns([2.2, 1.5, 1.3, 1.0], vertical_alignment="center")
        with col1:
            st.markdown(f"<div class='cell-placa'>{placa}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='cell-data'>{hora_fmt}</div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='cell-data'>{data_fmt}</div>", unsafe_allow_html=True)

        # Botão "Ver" que alterna a área expandida deste item.
        with col4:
            if st.button("Ver", key=f"toggle_{i}"):
                st.session_state[f"open_{i}"] = not st.session_state[f"open_{i}"]

        # Área expandida: exibe imagem (crop da placa) se existir; senão, um aviso.
        if st.session_state[f"open_{i}"]:
            if img:
                st.image(img, caption=f"Crop da placa {placa}", use_container_width=True)
            else:
                st.info("Nenhuma imagem disponível para este registro.")

        # Separador visual entre linhas.
        st.markdown("<div class='row-sep'></div>", unsafe_allow_html=True)
