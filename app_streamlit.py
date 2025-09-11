import os, hashlib
from datetime import datetime, date
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

from src.pipeline import process_image, inner_crop, annotate
from src.detect import find_plate_bbox, crop_bbox
from src.ocr import best_plate
from src.db import SessionLocal, AccessRecord

ROOT = Path(__file__).resolve().parent

st.set_page_config(page_title="ALPR - Leitura de Placas", layout="centered")
st.title("Leitura Automática de Placas (ALPR) — Demo")

tab1, tab2 = st.tabs(["📷 Processar imagem", "🔎 Consultar registros"])

# ---------------------------
# Utils
# ---------------------------
def bgr2rgb(img_bgr):
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

def show_hist(gray, title):
    fig = plt.figure(figsize=(6, 3))
    plt.hist(gray.ravel(), bins=256, range=(0, 255))
    plt.title(title)
    plt.xlabel("Intensidade"); plt.ylabel("Contagem")
    st.pyplot(fig)
    plt.close(fig)

def save_upload_once(img_bgr, file_bytes) -> Path:
    """
    Salva a imagem enviada apenas quando o usuário clica em Processar.
    Usa hash do conteúdo para evitar múltiplos uploads idênticos.
    """
    h = hashlib.md5(file_bytes).hexdigest()[:12]
    images_dir = ROOT / "data" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    path = images_dir / f"upload_{h}.jpg"
    if not path.exists():
        _ = cv2.imwrite(str(path), img_bgr)  # evita imprimir retorno
    return path

# ---------------------------
# TAB 1 — Processar imagem
# ---------------------------
with tab1:
    st.subheader("Processar nova imagem")

    # manter upload entre reruns do Streamlit
    if "upload_bytes" not in st.session_state:
        st.session_state.upload_bytes = None

    f = st.file_uploader("Selecione uma imagem (.jpg/.jpeg/.png)", type=["jpg","jpeg","png"])
    if f is not None:
        st.session_state.upload_bytes = f.getvalue()

    if st.session_state.upload_bytes:
        arr = np.frombuffer(st.session_state.upload_bytes, np.uint8)
        img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        st.image(bgr2rgb(img_bgr), caption="Pré-visualização", width="stretch")

        # ---------- Painel PDI (estilo notebook) ----------
        with st.expander("🔬 Análise PDI (modo notebook)", expanded=False):
            h, w = img_bgr.shape[:2]
            st.write(f"**Dimensões:** {h} x {w}")

            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            st.write(f"**Min/Max (grayscale):** {int(gray.min())} / {int(gray.max())}")

            col1, col2 = st.columns(2)
            with col1:
                st.image(gray, caption="Grayscale", width="stretch", clamp=True, channels="GRAY")
                show_hist(gray, "Histograma - Original")

            # Equalização global
            eq = cv2.equalizeHist(gray)
            with col2:
                st.image(eq, caption="Equalização global", width="stretch", clamp=True, channels="GRAY")
                show_hist(eq, "Histograma - Equalizada")

            # CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray)
            st.image(clahe, caption="CLAHE", width="stretch", clamp=True, channels="GRAY")
            show_hist(clahe, "Histograma - CLAHE")

            # Detecção + crop + candidatos OCR (sem gravar nada ainda)
            bbox = find_plate_bbox(img_bgr)
            crop = crop_bbox(img_bgr, bbox) if bbox is not None else img_bgr.copy()
            ocr_input = inner_crop(crop, ratio=0.08)
            p_prev, c_prev, cands_prev = best_plate(ocr_input)
            st.write(f"**Candidatos OCR (topo):** {cands_prev[:5]}")
            det_prev = annotate(img_bgr, bbox, p_prev or "")
            st.image(bgr2rgb(det_prev), caption="Detecção + texto (pré-processo)", width="stretch")
            st.image(bgr2rgb(ocr_input), caption="Recorte usado no OCR (pré-processo)", width="stretch")
        # ---------- fim painel PDI ----------

        # botão processar — só aqui salvamos e rodamos pipeline completa
        if st.button("Processar"):
            tmp_path = save_upload_once(img_bgr, st.session_state.upload_bytes)
            with st.spinner("Processando..."):
                res = process_image(str(tmp_path))
            st.success(f"Placa: {res['plate_text'] or '(sem leitura)'} | confiança: {res['confidence']:.2f} | id={res['id']}")

            if res.get("annotated_path") and os.path.exists(res["annotated_path"]):
                st.image(res["annotated_path"], caption="Imagem anotada", width="stretch")
            if res.get("crop_path") and os.path.exists(res["crop_path"]):
                st.image(res["crop_path"], caption="Recorte utilizado no OCR", width="stretch")

# ---------------------------
# TAB 2 — Consultar registros
# ---------------------------
with tab2:
    st.subheader("Consultar registros")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        plate_filter = st.text_input("Placa contém", "").upper().strip()
    with col2:
        dfrom = st.date_input("De", value=date.today().replace(day=1))
    with col3:
        dto = st.date_input("Até", value=date.today())

    group_latest = st.checkbox("Agrupar por placa (mostrar só o mais recente)", value=False)

    if st.button("Buscar"):
        s = SessionLocal()
        try:
            q = s.query(AccessRecord)
            if plate_filter:
                q = q.filter(AccessRecord.plate_text.like(f"%{plate_filter}%"))
            dfrom_dt = datetime.combine(dfrom, datetime.min.time())
            dto_dt = datetime.combine(dto, datetime.max.time())
            q = q.filter(AccessRecord.created_at >= dfrom_dt)
            q = q.filter(AccessRecord.created_at <= dto_dt)
            rows = q.order_by(AccessRecord.id.desc()).limit(400).all()
        finally:
            s.close()

        if group_latest:
            latest = {}
            for r in rows:
                key = (r.plate_text or "(sem)")
                if key not in latest or r.created_at > latest[key].created_at:
                    latest[key] = r
            rows = list(latest.values())

        if not rows:
            st.info("Nenhum registro encontrado para o filtro informado.")
        else:
            for r in rows:
                with st.container(border=True):
                    st.write(f"**#{r.id}** — **{r.plate_text or '(sem leitura)'}** "
                             f"(conf.={r.confidence:.2f}) — {r.created_at:%Y-%m-%d %H:%M}")
                    cols = st.columns(2)
                    if r.annotated_path and os.path.exists(r.annotated_path):
                        cols[0].image(r.annotated_path, caption="Anotada", width="stretch")
                    if r.plate_crop_path and os.path.exists(r.plate_crop_path):
                        cols[1].image(r.plate_crop_path, caption="Recorte", width="stretch")
