import streamlit as st
from src.components.filtrosBuscar import buscar
from src.components.registrosTable import registroTable
from src.controllers.placaController import PlacaController

class consultarRegistroPage:
    def app():
        st.title("Consultar Registros")

        # agora buscar() já devolve dict pronto
        filtros = buscar()

        # consulta real no banco
        registros = PlacaController.consultarRegistros(
            arg=filtros,
            data_inicio=filtros.get("data_inicio"),
            data_fim=filtros.get("data_fim"),
        )

        registroTable(registros)

