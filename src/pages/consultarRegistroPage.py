import streamlit as st
from src.components.filtrosBuscar import filtros_busca
from src.components.registrosTable import registros_table
from src.controllers.placaController import PlacaController

class consultarRegistroPage:
    def app():
        st.title("Consultar Registros")

        filtros = filtros_busca()
        registros = [
            {"placa": "ABC-1234", "data": "12/09/2025 10:14:00", "imagem": "src/static/crops/crop_teste1.png"},
            {"placa": "XYZ-5678", "data": "12/09/2025 10:20:00", "imagem": "src/static/crops/crop_teste1.png"},
            {"placa": "JKL-9012", "data": "12/09/2025 10:25:00", "imagem": "src/static/crops/crop_teste1.png"},  # sem imagem
        ]

        #registros = PlacaController.consultarRegistros(filtros)

        registros_table(registros)
