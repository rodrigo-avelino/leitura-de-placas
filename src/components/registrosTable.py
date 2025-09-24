import os
import streamlit as st
from datetime import datetime

# ---------- COMPONENTE ----------
def registroTable(registros):
    # Título
    st.markdown(
        f"<h3>Consulta de Placas <span style='color:#69a6ff'>({len(registros)})</span></h3>",
        unsafe_allow_html=True
    )

    # --- estilos ---
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

    # cabeçalho
    c1, c2, c3, c4 = st.columns([2.2, 1.5, 1.3, 1.0])
    with c1: st.markdown("<div class='header'>Placa</div>", unsafe_allow_html=True)
    with c2: st.markdown("<div class='header'>Hora</div>", unsafe_allow_html=True)
    with c3: st.markdown("<div class='header'>Data</div>", unsafe_allow_html=True)
    with c4: st.markdown("<div class='header'>Visualizar</div>", unsafe_allow_html=True)
    st.markdown("<div class='row-sep'></div>", unsafe_allow_html=True)

    # linhas
    for i, r in enumerate(registros):
        placa = r["placa"]
        data  = r["data"]
        img   = r.get("imagem")

        # formata data se vier no formato ISO
        try:
            dt = datetime.strptime(data, "%Y-%m-%d %H:%M:%S")
            hora_fmt = dt.strftime("%H:%M")
            data_fmt = dt.strftime("%d.%m.%y")
        except Exception:
            hora_fmt = ""
            data_fmt = data

        # estado do toggle da linha
        st.session_state.setdefault(f"open_{i}", False)

        col1, col2, col3, col4 = st.columns([2.2, 1.5, 1.3, 1.0], vertical_alignment="center")
        with col1: st.markdown(f"<div class='cell-placa'>{placa}</div>", unsafe_allow_html=True)
        with col2: st.markdown(f"<div class='cell-data'>{hora_fmt}</div>", unsafe_allow_html=True)
        with col3: st.markdown(f"<div class='cell-data'>{data_fmt}</div>", unsafe_allow_html=True)

        # botão "Ver" (rótulo fixo)
        with col4:
            if st.button("Ver", key=f"toggle_{i}"):
                st.session_state[f"open_{i}"] = not st.session_state[f"open_{i}"]

        # área expandida com o crop (abaixo da linha)
        if st.session_state[f"open_{i}"]:
            if img:
                st.image(img, caption=f"Crop da placa {placa}", use_container_width=True)
            else:
                st.info("Nenhuma imagem disponível para este registro.")

        # separador entre linhas
        st.markdown("<div class='row-sep'></div>", unsafe_allow_html=True)