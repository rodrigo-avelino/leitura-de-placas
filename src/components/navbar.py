import streamlit as st

def navbar(active_page: str):
    st.markdown("""
        <!-- Font Awesome (opcional) -->
        <link rel="stylesheet"
              href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" />

        <style>
        /* Container do card */
        .navbar {
            max-width: 1200px;
            margin: 0 auto 22px auto;
            padding: 10px;
            background: #12161b;
            border-radius: 14px;
            box-shadow: 0 6px 18px rgba(0,0,0,.35);
            overflow-x: auto;           /* mantém horizontal em telas pequenas */
            -webkit-overflow-scrolling: touch; /* scroll suave no iOS */
        }
        /* Remove barra de rolagem visual (opcional) */
        .navbar::-webkit-scrollbar { height: 0px; }

        /* Faixa que segura os botões */
        .nav-track {
            display: flex;
            gap: 14px;
            justify-content: center;
            align-items: center;
            flex-wrap: nowrap;          /* nunca quebra a linha */
            min-width: 420px;           /* evita “apertar” demais os botões */
        }

        /* Botão */
        .nav-item {
            flex: 1 1 0;                /* mesmas larguras */
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            padding: 14px 24px;
            border: 1px solid rgba(255,255,255,.06);
            border-radius: 10px;
            background: #181d23;
            color: #e9eef5;
            font-size: 1rem;
            font-weight: 600;
            letter-spacing: .2px;
            cursor: pointer;
            user-select: none;
            text-decoration: none;
            outline: none;
            transition: transform .12s ease, background .18s ease, border-color .18s ease, box-shadow .18s ease;
            white-space: nowrap;        /* mantém o texto numa linha */
        }
        .nav-item:hover {
            background: #212730;
            border-color: rgba(255,255,255,.12);
            transform: translateY(-1px);
            box-shadow: 0 8px 18px rgba(0,0,0,.25);
        }
        .nav-item:active {
            transform: translateY(0);
        }

        /* Estado ativo */
        .nav-item.active {
            background: #2a313c;
            border-color: rgba(255,255,255,.18);
            box-shadow: inset 0 0 0 1px rgba(255,255,255,.06), 0 10px 22px rgba(0,0,0,.28);
        }

        /* Pequenas otimizações responsivas (continua horizontal, só ajusta padding) */
        @media (max-width: 680px) {
            .nav-item { padding: 12px 18px; font-size: .95rem; }
            .nav-track { gap: 10px; min-width: 360px; }
        }
        </style>

        <div class="navbar">
          <form class="nav-track" method="post">
            <button class="nav-item {a1}" name="page" value="processar" type="submit">
              <i class="fa-solid fa-camera"></i> Processar Imagem
            </button>
            <button class="nav-item {a2}" name="page" value="consultar" type="submit">
              <i class="fa-solid fa-magnifying-glass"></i> Consultar Registros
            </button>
          </form>
        </div>
    """.replace("{a1}", "active" if active_page == "processar" else "")
       .replace("{a2}", "active" if active_page == "consultar" else ""),
       unsafe_allow_html=True)
