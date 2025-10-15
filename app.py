import streamlit as st
from src.components.navbar import navbar
from src.pages.processarImagemPage import ProcessarImagemPage
from src.pages.consultarRegistroPage import consultarRegistroPage
from src.pages.debugPage import app as debugApp # 1. ADICIONE ESTA IMPORTAÇÃO
from src.pages.debugDeteccaoPage import app as debugDeteccaoApp 

# Configurações globais da aplicação Streamlit:
st.set_page_config(page_title="Sistema de Reconhecimento de Placas", layout="wide")

# Lê o parâmetro de querystring ?page=... para decidir qual página mostrar.
page = st.query_params.get("page", "processar")

if isinstance(page, list):
    page = page[0]

st.session_state.page = page

# Renderiza a barra de navegação (Navbar)
navbar(st.session_state.page)

# --- 2. BLOCO DE ROTEAMENTO MODIFICADO ---
# Roteamento simples:
if st.session_state.page == "processar":
    ProcessarImagemPage.app()
elif st.session_state.page == "debug":
    debugApp()
elif st.session_state.page == "debug_deteccao": # 2. ADICIONE ESTE BLOCO
    debugDeteccaoApp()
else: # Por padrão, qualquer outra coisa cai na consulta
    consultarRegistroPage.app()