import streamlit as st

from src.pages.processarImagemPage import app as processar_imagem_app
from src.pages.consultarRegistroPage import app as consultar_registro_app


# ---- Configuração geral da aplicação ----
st.set_page_config(
    page_title="Reconhecimento de Placas",
    page_icon="🚘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---- Sidebar ----
st.sidebar.title("📂 Navegação")
pagina = st.sidebar.radio(
    "Escolha a página:",
    ("🔍 Processar Imagem", "📑 Consultar Registros")
)

# ---- Roteamento ----
if pagina == "🔍 Processar Imagem":
    processar_imagem_app()
elif pagina == "📑 Consultar Registros":
    consultar_registro_app()
