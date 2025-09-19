import streamlit as st
from src.pages import processarImagemPage, consultarRegistroPage
from src.components.navbar import navbar

st.set_page_config(page_title="Sistema de Reconhecimento de Placas", layout="wide")

from streamlit import session_state

if "page" not in session_state:
    session_state.page = "processar"

# Navbar modular
navbar(session_state.page)

# Captura navegação por POST
if st.session_state.get("page") != session_state.page:
    session_state.page = st.session_state.get("page", session_state.page)

# Renderizar página ativa
if session_state.page == "processar":
    processarImagemPage.app()
elif session_state.page == "consultar":
    consultarRegistroPage.app()
