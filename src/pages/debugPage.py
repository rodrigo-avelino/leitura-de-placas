import streamlit as st
import cv2
import numpy as np
from src.controllers.placaController import _read_image_bgr

# Importa todos os serviços necessários para a detecção e recorte
from src.services.preprocessamento import Preprocessamento
from src.services.bordas import Bordas
from src.services.contornos import Contornos
from src.services.filtrarContornos import FiltrarContornos
from src.services.recorte import Recorte

def app():
    st.title("🔬 Laboratório de Pré-processamento e Binarização")

    st.info(
        "Use esta página para testar diferentes técnicas de processamento em "
        "tempo real e encontrar os melhores parâmetros para o pipeline."
    )

    # --- Uploader da Imagem ---
    uploaded_file = st.file_uploader(
        "Selecione a imagem COMPLETA do veículo", # Instrução atualizada
        type=["png", "jpg", "jpeg"],
    )

    if not uploaded_file:
        st.warning("Por favor, envie uma imagem para começar os testes.")
        st.stop()

    # --- ETAPA 1: Executa o pipeline de DETECÇÃO e RECORTE ---
    imagem_original_bgr = _read_image_bgr(uploaded_file)
    
    with st.spinner("Detectando e recortando a placa..."):
        preproc = Preprocessamento.executar(imagem_original_bgr)
        edges = Bordas.executar(preproc)
        contours = Contornos.executar(edges)
        candidatos = FiltrarContornos.executar(contours, imagem_original_bgr)

    if not candidatos:
        st.error("Nenhuma placa foi detectada na imagem. Tente uma imagem diferente.")
        st.stop()
    
    # Pega o melhor candidato e faz o recorte
    best_quad = candidatos[0].get("quad")
    crop_bgr = Recorte.executar(imagem_original_bgr, best_quad)
    crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)

    st.subheader("Recorte da Placa Gerado pelo Pipeline")
    st.image(crop_rgb, caption="Esta é a imagem que será usada para os testes abaixo.")

    st.divider()
    st.subheader("Bancada de Testes de Binarização")

    # --- Sidebar com os Controles dos Filtros ---
    st.sidebar.header("Controles dos Filtros")
    st.sidebar.subheader("1. Suavização (Opcional)")
    use_bilateral = st.sidebar.checkbox("Ativar Filtro Bilateral", value=True)
    if use_bilateral:
        d = st.sidebar.slider("Diâmetro (d)", 1, 15, 5, 2)
        sigma_color = st.sidebar.slider("Sigma Color", 1, 200, 75)
        sigma_space = st.sidebar.slider("Sigma Space", 1, 200, 75)

    st.sidebar.subheader("2. Contraste Morfológico")
    tipo_filtro_morph = st.sidebar.selectbox("Tipo de Filtro", ["Nenhum", "Black-hat", "Top-hat"])
    kernel_w = st.sidebar.slider("Largura do Kernel", 1, 50, 13)
    kernel_h = st.sidebar.slider("Altura do Kernel", 1, 50, 5)

    st.sidebar.subheader("3. Binarização Final")
    tipo_bin = st.sidebar.selectbox("Método de Binarização", ["Simples (Global)", "Otsu", "Adaptativo (Gaussiano)"])
    if tipo_bin == "Simples (Global)":
        limiar = st.sidebar.slider("Limiar (Threshold)", 0, 255, 15)
    elif tipo_bin == "Adaptativo (Gaussiano)":
        block_size = st.sidebar.slider("Tamanho do Bloco", 3, 51, 21, 2)
        const_c = st.sidebar.slider("Constante C", -30, 30, 10)

    # --- Pipeline de Processamento (agora usando o CROP como entrada) ---
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    
    base_image = gray.copy()
    if use_bilateral:
        base_image = cv2.bilateralFilter(base_image, d, sigma_color, sigma_space)

    morph_image = base_image
    if tipo_filtro_morph != "Nenhum":
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_w, kernel_h))
        if tipo_filtro_morph == "Black-hat":
            morph_image = cv2.morphologyEx(base_image, cv2.MORPH_BLACKHAT, kernel)
        elif tipo_filtro_morph == "Top-hat":
            morph_image = cv2.morphologyEx(base_image, cv2.MORPH_TOPHAT, kernel)
            
    if tipo_bin == "Simples (Global)":
        _, imagem_final_bin = cv2.threshold(morph_image, limiar, 255, cv2.THRESH_BINARY)
    elif tipo_bin == "Otsu":
        _, imagem_final_bin = cv2.threshold(morph_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif tipo_bin == "Adaptativo (Gaussiano)":
        imagem_final_bin = cv2.adaptiveThreshold(morph_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, const_c)

    # --- Exibição dos Resultados ---
    st.markdown("##### Resultados Intermediários")
    cols = st.columns(4)
    with cols[0]:
        st.image(gray, channels="GRAY", caption="1. Grayscale do Recorte")
    with cols[1]:
        st.image(base_image, channels="GRAY", caption="2. Após Suavização")
    with cols[2]:
        st.image(morph_image, channels="GRAY", caption="3. Após Contraste")
    with cols[3]:
        st.image(imagem_final_bin, channels="GRAY", caption="4. Binarização Final")