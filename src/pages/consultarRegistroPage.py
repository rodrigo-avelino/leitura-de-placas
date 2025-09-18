import streamlit as st
from src.components.filtrosBuscar import filtros_busca
from src.components.registrosTable import registros_table
from src.controllers.placaController import PlacaController

def app():
    st.title("📑 Consultar Registros")

    filtros = filtros_busca()
    registros = PlacaController.consultarRegistros(filtros)

    registros_table(registros)
