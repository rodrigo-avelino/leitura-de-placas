import streamlit as st
from src.components.filtrosBuscar import buscar
from src.components.registrosTable import registroTable
from src.controllers.placaController import PlacaController

class consultarRegistroPage:
    def app():
        # Título da página
        st.title("Consultar Registros")

        # ------------------------------------------------------------------
        # 1) Coleta de filtros na UI
        # 'buscar()' renderiza os inputs (placa, data inicial, data final)
        # e retorna um dicionário já normalizado, ex.:
        # {
        #   "placa": "POX",
        #   "data_inicio": datetime(...),  # pode ser None
        #   "data_fim": datetime(...),     # pode ser None (geralmente 23:59:59)
        # }
        # ------------------------------------------------------------------
        filtros = buscar()

        # ------------------------------------------------------------------
        # 2) Consulta no banco
        # Passamos 'arg=filtros' para o controller, que entende dict ou string.
        # Também enviamos explicitamente data_inicio/data_fim para manter
        # compatibilidade com a assinatura do método (MVP).
        #
        # O controller aplica os filtros:
        #  - placa: ILIKE '%<placa>%'
        #  - intervalo de datas: created_at >= data_inicio AND <= data_fim
        #  e devolve uma lista de dicts no formato:
        #  {
        #    "placa": "POX4G21",
        #    "data": "YYYY-MM-DD HH:MM:SS",  # UTC (UI pode converter/fmt)
        #    "imagem": "data:image/png;base64,..."  # crop opcional
        #  }
        # ------------------------------------------------------------------
        registros = PlacaController.consultarRegistros(
            arg=filtros,
            data_inicio=filtros.get("data_inicio"),
            data_fim=filtros.get("data_fim"),
        )

        # ------------------------------------------------------------------
        # 3) Renderização da tabela
        # 'registroTable' recebe a lista de registros e cuida da apresentação:
        # cabeçalho, linhas, toggle de "Ver" para abrir o crop (quando existir),
        # formatação de data/hora, etc.
        # ------------------------------------------------------------------
        registroTable(registros)
