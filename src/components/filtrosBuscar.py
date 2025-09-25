import streamlit as st
from datetime import datetime
# a função buscar faz a interface de filtros de busca
def buscar():
    st.subheader("Filtros de Busca")
    filtro_placa = st.text_input("Buscar por placa")
# aqui acontece a seleção de datas
    col1, col2 = st.columns(2)
    with col1:
        data_ini = st.date_input(
            "Data inicial",
            value=None,
            format="DD/MM/YYYY"
        )
#já aqui é a data final
    with col2:
        data_fim = st.date_input(
            "Data final",
            value=None,
            format="DD/MM/YYYY"
        )

    # converter date para datetime (ou deixar None)
    data_inicio = datetime.combine(data_ini, datetime.min.time()) if data_ini else None
    data_final  = datetime.combine(data_fim, datetime.max.time()) if data_fim else None
# retorna um dicionario com os filtros
    return {
        "placa": filtro_placa if filtro_placa else None,
        "data_inicio": data_inicio,
        "data_fim": data_final
    }
