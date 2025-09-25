import streamlit as st
from src.components.navbar import navbar
from src.pages.processarImagemPage import ProcessarImagemPage
from src.pages.consultarRegistroPage import consultarRegistroPage

# Configurações globais da aplicação Streamlit:
# - Título da aba do navegador
# - Layout "wide" para aproveitar toda a largura da página
st.set_page_config(page_title="Sistema de Reconhecimento de Placas", layout="wide")

# Lê o parâmetro de querystring ?page=... para decidir qual página mostrar.
# Se não vier nada, padrão é "processar".
page = st.query_params.get("page", "processar")

# Em alguns cenários o Streamlit pode entregar uma lista (ex.: page=[...]).
# Garante que 'page' seja string.
if isinstance(page, list):
    page = page[0]

# Mantém a página atual no session_state para que outros componentes possam consultar
# (e para persistir a navegação entre reruns).
st.session_state.page = page

# Renderiza a barra de navegação (Navbar) já indicando qual aba está ativa.
# A navbar provavelmente usa esse valor para destacar a opção selecionada
# e/ou para construir os links com querystring.
navbar(st.session_state.page)

# Roteamento simples:
# - Se a página corrente for "processar", renderiza a tela de processamento de imagem.
# - Caso contrário, abre a tela de consulta de registros.
if st.session_state.page == "processar":
    ProcessarImagemPage.app()
else:
    consultarRegistroPage.app()
