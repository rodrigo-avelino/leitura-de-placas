import streamlit as st
from src.components.navbar import navbar
from src.pages.processarImagemPage import ProcessarImagemPage
from src.pages.consultarRegistroPage import consultarRegistroPage

st.set_page_config(page_title="Sistema de Reconhecimento de Placas", layout="wide")

page = st.query_params.get("page", "processar")
if isinstance(page, list):
    page = page[0]
st.session_state.page = page

navbar(st.session_state.page)

if st.session_state.page == "processar":
    ProcessarImagemPage.app()
else:
    consultarRegistroPage.app()
