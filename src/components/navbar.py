# Em src/components/navbar.py

import streamlit as st

def _go(page: str):
    st.query_params["page"] = page
    st.session_state.page = page

def navbar(active_page: str):
    st.markdown(
        """
        <style>
        /* ... (todo o seu código CSS continua o mesmo aqui) ... */
        .navbar-row {
          max-width: 1820px;
          margin: 0 auto 22px auto !important;
          padding: 12px !important;
          border-radius: 16px !important;
          background: rgba(24, 29, 35, .75) !important;
          border: 1px solid rgba(255,255,255,.10) !important;
          box-shadow: 0 8px 26px rgba(0,0,0,.35) !important;
          backdrop-filter: blur(6px);
          -webkit-backdrop-filter: blur(6px);
        }
        .navbar-row > div:first-child { padding: 0 !important; }
        .navbar-row [data-testid="baseButton-primary"],
        .navbar-row [data-testid="baseButton-secondary"]{
            flex: 1 1 0;
            display: flex; align-items: center; justify-content: center; gap: 10px;
            width: 100%;
            padding: 14px 24px;
            border-radius: 12px;
            color: #e9eef5;
            background: #181d23;
            border: 1px solid rgba(255,255,255,.10);
            font-size: 1rem; font-weight: 600; letter-spacing: .2px;
            cursor: pointer; user-select: none; text-decoration: none; outline: none;
            white-space: nowrap;
            transition: transform .12s ease, background .18s ease, border-color .18s ease, box-shadow .18s ease, filter .18s ease;
        }
        .navbar-row [data-testid="baseButton-primary"]:hover,
        .navbar-row [data-testid="baseButton-secondary"]:hover{
            background: #212730;
            border-color: rgba(255,255,255,.18);
            transform: translateY(-1px);
            box-shadow: 0 14px 28px rgba(0,0,0,.40);
            filter: saturate(1.02);
        }
        .navbar-row [data-testid="baseButton-primary"]{
            background: #2a313c;
            border-color: rgba(255,255,255,.22);
            box-shadow: inset 0 0 0 1px rgba(255,255,255,.06), 0 10px 22px rgba(0,0,0,.28);
            position: relative;
        }
        .navbar-row [data-testid="baseButton-primary"]::after{
            content:"";
            position:absolute; left: 16px; right: 16px; bottom: 6px; height: 2px;
            background: linear-gradient(135deg, #6EE7F9, #A78BFA, #F472B6, #FDE68A);
            border-radius: 2px; opacity: .9;
        }
        @media (max-width: 720px){
          .navbar-row [data-testid="baseButton-primary"],
          .navbar-row [data-testid="baseButton-secondary"]{
              padding: 12px 18px; font-size: .95rem;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- CORREÇÃO APLICADA AQUI ---
    # Mudamos de 2 para 3 colunas e adicionamos o novo botão
    c1, c2, c3, c4 = st.columns(4, gap="small")
    with c1:
        st.button(
            "Processar Imagem",
            key="nav_processar",
            # A nova versão do Streamlit usa 'width' em vez de 'use_container_width'
            # No entanto, para st.button, o parâmetro correto é 'use_container_width'
            use_container_width=True,
            type=("primary" if active_page == "processar" else "secondary"),
            on_click=_go, args=("processar",),
        )
    with c2:
        st.button(
            "Consultar Registros",
            key="nav_consultar",
            use_container_width=True,
            type=("primary" if active_page == "consultar" else "secondary"),
            on_click=_go, args=("consultar",),
        )
    with c3:
        st.button(
            "Laboratório de Debug",
            key="nav_debug",
            use_container_width=True,
            type=("primary" if active_page == "debug" else "secondary"),
            on_click=_go, args=("debug",),
        )
    with c4: # NOVO BOTÃO
        st.button(
            "Debug Detecção",
            key="nav_debug_deteccao",
            use_container_width=True,
            type=("primary" if active_page == "debug_deteccao" else "secondary"),
            on_click=_go, args=("debug_deteccao",),
        )

    # O script para aplicar a classe .navbar-row continua o mesmo
    st.markdown(
        """
        <script>
        (function() {
          const ifr = window.frameElement; if (!ifr) return;
          const root = ifr.parentElement; if (!root) return;
          const blocks = root.querySelectorAll('[data-testid="stHorizontalBlock"]');
          const last = blocks[blocks.length - 1];
          if (last && !last.classList.contains('navbar-row')) last.classList.add('navbar-row');
        })();
        </script>
        """,
        unsafe_allow_html=True,
    )