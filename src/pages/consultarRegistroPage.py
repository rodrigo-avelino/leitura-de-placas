import streamlit as st
from datetime import datetime
from src.controllers.placaController import PlacaController

def app():
    st.title("🗂️ Consultar Registros")

    # filtros
    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        placa_filtro = st.text_input("Buscar por placa", value="")
    with col2:
        data_inicio = st.date_input("Data inicial", value=None)
    with col3:
        data_fim = st.date_input("Data final", value=None)

    # converter para datetime (ou None)
    di = datetime.combine(data_inicio, datetime.min.time()) if data_inicio else None
    df = datetime.combine(data_fim, datetime.min.time()) if data_fim else None

    # buscar
    registros = PlacaController.consultarRegistros(
        placa=placa_filtro.strip() or None,
        data_inicio=di,
        data_fim=df
    )

    st.subheader(f"📄 Registros Encontrados ({len(registros)})")

    if not registros:
        st.info("Nenhum registro encontrado para os filtros informados.")
        return

    # listar resultados
    for r in registros:
        with st.container(border=True):
            colA, colB, colC = st.columns([2,1,1])
            with colA:
                st.markdown(f"**Placa:** {r['placa']}")
                st.markdown(f"**Data/Hora:** {r['data_hora']}")
            with colB:
                st.markdown(f"**Score:** {r['score']:.3f}")

            # Se você habilitou os bytes no controller, pode mostrar as imagens:
            # if 'plate_crop_image' in r and r['plate_crop_image']:
            #     st.image(r['plate_crop_image'], caption="Recorte da placa", use_container_width=False)
            # elif 'source_image' in r and r['source_image']:
            #     st.image(r['source_image'], caption="Imagem original", use_container_width=True)
