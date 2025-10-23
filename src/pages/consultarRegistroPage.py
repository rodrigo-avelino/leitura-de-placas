import streamlit as st
from src.components.filtrosBuscar import buscar
from src.components.registrosTable import registroTable
from src.controllers.placaController import PlacaController

# --- Função de Ação ---
# Esta função lida com a exclusão e força o refresh da página.
def handle_delete(registro_id):
    """
    Função chamada quando um registro é marcado para exclusão.
    Chama o Controller e atualiza a sessão.
    """
    if registro_id is None:
        return

    try:
        # 1. CHAMA O MÉTODO DE EXCLUSÃO DO CONTROLLER
        success = PlacaController.excluirRegistro(registro_id)
        
        if success:
            st.success(f"Registro '{registro_id}' excluído com sucesso!")
            # 2. Forçar uma nova consulta e renderização
            st.session_state.refresh_data = True 
        else:
            st.error(f"Falha ao excluir o registro '{registro_id}'.")
            
    except Exception as e:
        st.error(f"Erro inesperado ao excluir o registro '{registro_id}': {e}")


class consultarRegistroPage:
    def app():
        # --- Configuração Inicial de Session State ---
        # Usado para forçar a re-consulta de dados após uma exclusão.
        if 'refresh_data' not in st.session_state:
            st.session_state.refresh_data = True
        
        # Usado para armazenar a lista de registros para não recarregar em cada interação.
        if 'registros_data' not in st.session_state:
            st.session_state.registros_data = []

        st.title("Consultar Registros")

        # ------------------------------------------------------------------
        # 1) Coleta de filtros na UI
        # ------------------------------------------------------------------
        # A função buscar() deve retornar um dicionário com os filtros.
        filtros = buscar()

        # ------------------------------------------------------------------
        # 2) Lógica de Exclusão
        # Verifica se o componente registroTable marcou um ID para exclusão.
        # ------------------------------------------------------------------
        if 'delete_id' in st.session_state and st.session_state.delete_id is not None:
            # Chama a função de exclusão
            handle_delete(st.session_state.delete_id)
            # Limpa a variável de estado para evitar exclusões repetidas
            st.session_state.delete_id = None # Limpa após o uso

        # ------------------------------------------------------------------
        # 3) Consulta no banco
        # Só executa se for o primeiro carregamento ou se houver um refresh (após exclusão).
        # ------------------------------------------------------------------
        if st.session_state.refresh_data:
            with st.spinner('Consultando registros...'):
                registros = PlacaController.consultarRegistros(
                    arg=filtros,
                    data_inicio=filtros.get("data_inicio"),
                    data_fim=filtros.get("data_fim"),
                )
            
            # Atualiza o estado da sessão com os novos dados e reseta o flag de refresh
            st.session_state.registros_data = registros
            st.session_state.refresh_data = False
        
        # ------------------------------------------------------------------
        # 4) Renderização da tabela
        # ------------------------------------------------------------------
        if st.session_state.registros_data:
            registroTable(st.session_state.registros_data)
        elif not st.session_state.refresh_data:
             st.info("Nenhum registro encontrado com os filtros aplicados.")