import streamlit as st

def filtros_busca():
    st.subheader("🔎 Filtros de Busca")
    filtro_placa = st.text_input("Buscar por placa")
    col1, col2 = st.columns(2)
    with col1:
        data_ini = st.date_input("Data inicial")
    with col2:
        data_fim = st.date_input("Data final")
    return filtro_placa, data_ini, data_fim
