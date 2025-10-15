# src/pages/debugDeteccaoPage.py

import streamlit as st
import cv2
import numpy as np
from src.controllers.placaController import _read_image_bgr, _overlay_contours

# Importa os serviços
from src.services.preprocessamento import Preprocessamento
from src.services.bordas import Bordas
from src.services.contornos import Contornos
from src.services.filtrarContornos import FiltrarContornos
from src.services.segmentacao import Segmentacao # <-- NOVA IMPORTAÇÃO

def _overlay_filled_quad(image, quad, color=(0, 255, 0), alpha=0.4):
    overlay, output = image.copy(), image.copy()
    cv2.fillPoly(overlay, [np.array(quad, dtype=np.int32)], color)
    cv2.addWeighted(overlay, alpha, output, 1 - alpha, 0, output)
    return output

def app():
    st.set_page_config(layout="wide")
    st.title("🔬 Laboratório de Detecção e Ranqueamento")
    st.info("Use esta página para analisar visualmente por que o sistema está escolhendo um candidato em vez de outro.")

    uploaded_file = st.file_uploader("Selecione uma imagem", type=["png", "jpg", "jpeg"])
    if not uploaded_file:
        st.warning("Por favor, envie uma imagem para começar.")
        st.stop()

    img_bgr = _read_image_bgr(uploaded_file)
    preproc_img = Preprocessamento.executar(img_bgr)
    
    # Lógica de detecção
    canny_presets = [(50, 150), (100, 200), (150, 250)]
    todos_os_contornos = []
    for (t1, t2) in set(canny_presets):
        edges = Bordas.executar(preproc_img, threshold1=t1, threshold2=t2)
        todos_os_contornos.extend(Contornos.executar(edges))
        
    st.subheader("Visualização dos Candidatos")
    
    candidatos = FiltrarContornos.executar(todos_os_contornos, img_bgr)

    if not candidatos:
        st.warning("Nenhum candidato a placa foi encontrado.")
    else:
        img_com_overlays = img_bgr.copy()
        cores = [(0, 255, 0), (0, 255, 255), (255, 0, 0), (255, 0, 255), (255, 255, 0)]

        st.write("Os 5 melhores candidatos encontrados. O candidato **#1 (verde)** é o que o sistema escolhe.")
        for i, cand in enumerate(candidatos[:5]):
            quad = cand.get("quad")
            if quad is not None:
                cor = cores[i % len(cores)]
                img_com_overlays = _overlay_filled_quad(img_com_overlays, quad, color=cor, alpha=0.5)
                cv2.polylines(img_com_overlays, [np.array(quad, dtype=np.int32)], True, cor, 2)
                cv2.putText(img_com_overlays, f"#{i+1}", (int(quad[0][0]), int(quad[0][1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, cor, 2)

        st.image(img_com_overlays, caption="Top 5 Candidatos (Verde = #1)", channels="BGR", use_container_width=True)

        st.subheader("Análise Detalhada de Cada Candidato")
        for i, cand in enumerate(candidatos[:5]):
            score = cand.get('score', 0)
            with st.expander(f"Candidato #{i+1} - Score Final: {score:.3f}"):
                # --- INÍCIO DA NOVA SEÇÃO DE VISUALIZAÇÃO ---
                st.write("--- Análise da Segmentação ---")
                
                bin_image = cand.get("bin_image")
                if bin_image is not None and bin_image.size > 0:
                    # Segmenta os caracteres a partir da imagem binarizada
                    chars = Segmentacao.executar(bin_image)
                    
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.image(bin_image, caption="1. Resultado da Binarização", use_container_width=True)
                    
                    with c2:
                        if chars:
                            # Concatena as imagens dos caracteres horizontalmente para exibição
                            vis_chars = np.concatenate(chars, axis=1)
                            st.image(vis_chars, caption=f"2. Caracteres Segmentados ({len(chars)})", use_container_width=True)
                        else:
                            st.info("Nenhum caractere foi segmentado a partir da binarização.")
                else:
                    st.warning("Imagem binarizada não disponível para este candidato.")
                
                # --- FIM DA NOVA SEÇÃO ---

                st.write("--- Detalhes da Pontuação ---")
                detalhes = {
                    "Score Final": f"{score:.3f}",
                    "Score Geométrico": f"{cand.get('score_geom', 'N/A'):.3f}",
                    "Score de Segmentação": f"{cand.get('seg_score', 'N/A'):.3f}",
                    "Caracteres Encontrados": cand.get('num_chars', 'N/A'),
                    "Método": cand.get('method', 'N/A'),
                    "Padrão de Placa": cand.get('pattern', 'N/A'),
                }
                st.json(detalhes)