import streamlit as st

def registros_table(registros):
    st.subheader(f"📋 Registros Encontrados ({len(registros)})")
    for r in registros:
        placa = r["placa"]
        data = r["data"]
        status = r["status"]
        st.markdown(f"**{placa}** | {data} | :green[{status}]")
