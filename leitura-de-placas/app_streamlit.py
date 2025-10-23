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

# Raiz do projeto (pasta deste arquivo) — usado para salvar uploads
ROOT = Path(__file__).resolve().parent

# Configuração básica da página Streamlit
st.set_page_config(page_title="ALPR - Leitura de Placas", layout="centered")
st.title("Leitura Automática de Placas (ALPR) — Demo")

# Duas abas: 1) Processar imagem  2) Consultar registros no banco
tab1, tab2 = st.tabs(["📷 Processar imagem", "🔎 Consultar registros"])

# ---------------------------
# Utils (funções auxiliares)
# ---------------------------

def bgr2rgb(img_bgr):
    """OpenCV lê em BGR; Streamlit/Matplotlib esperam RGB. Converte para exibir corretamente."""
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

def show_hist(gray, title):
    """
    Mostra histograma de intensidades para uma imagem em escala de cinza.
    Útil para diagnosticar contraste/iluminação.
    """
    fig = plt.figure(figsize=(6, 3))
    plt.hist(gray.ravel(), bins=256, range=(0, 255))
    plt.title(title)
    plt.xlabel("Intensidade"); plt.ylabel("Contagem")
    st.pyplot(fig)    # renderiza o gráfico no Streamlit
    plt.close(fig)    # evita vazamento de figuras em memória

def save_upload_once(img_bgr, file_bytes) -> Path:
    """
    Salva a imagem enviada APENAS quando o usuário clica em Processar.
    Usa um hash (MD5) do conteúdo para evitar salvar múltiplas cópias idênticas.
    Retorna o caminho onde o arquivo foi salvo.
    """
    h = hashlib.md5(file_bytes).hexdigest()[:12]           # hash curto para nome do arquivo
    images_dir = ROOT / "data" / "images"                  # pasta para uploads processados
    images_dir.mkdir(parents=True, exist_ok=True)          # garante que a pasta exista
    path = images_dir / f"upload_{h}.jpg"
    if not path.exists():
        _ = cv2.imwrite(str(path), img_bgr)                # grava o arquivo (retorno ignorado)
    return path

# ---------------------------
# TAB 1 — Processar imagem
# ---------------------------
with tab1:
    st.subheader("Processar nova imagem")

    # Guardamos os bytes do upload no session_state para sobreviver a reruns do Streamlit
    if "upload_bytes" not in st.session_state:
        st.session_state.upload_bytes = None

    # Componente de upload (aceita jpg/jpeg/png)
    f = st.file_uploader("Selecione uma imagem (.jpg/.jpeg/.png)", type=["jpg","jpeg","png"])
    if f is not None:
        # Lê os bytes do arquivo e guarda em sessão
        st.session_state.upload_bytes = f.getvalue()

    # Se temos bytes carregados, exibimos preview e um painel de PDI
    if st.session_state.upload_bytes:
        # Decodifica bytes em array OpenCV (BGR)
        arr = np.frombuffer(st.session_state.upload_bytes, np.uint8)
        img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)

        # Pré-visualização da imagem enviada
        st.image(bgr2rgb(img_bgr), caption="Pré-visualização", width="stretch")

        # ---------- Painel PDI (estilo notebook) ----------
        # Bloco expandível com diagnósticos/transformações (não salva nada, apenas mostra)
        with st.expander("🔬 Análise PDI (modo notebook)", expanded=False):
            h, w = img_bgr.shape[:2]
            st.write(f"**Dimensões:** {h} x {w}")

            # Converte para tons de cinza e mostra estatísticas básicas
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            st.write(f"**Min/Max (grayscale):** {int(gray.min())} / {int(gray.max())}")

            # Duas colunas: original em cinza + igualada globalmente
            col1, col2 = st.columns(2)
            with col1:
                st.image(gray, caption="Grayscale", width="stretch", clamp=True, channels="GRAY")
                show_hist(gray, "Histograma - Original")

            # Equalização global (melhora contraste)
            eq = cv2.equalizeHist(gray)
            with col2:
                st.image(eq, caption="Equalização global", width="stretch", clamp=True, channels="GRAY")
                show_hist(eq, "Histograma - Equalizada")

            # CLAHE (equalização local adaptativa — melhor que global em muitas cenas)
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray)
            st.image(clahe, caption="CLAHE", width="stretch", clamp=True, channels="GRAY")
            show_hist(clahe, "Histograma - CLAHE")

            # Detecção do bounding box da placa (heurística do módulo detect)
            bbox = find_plate_bbox(img_bgr)

            # Recorte bruto com base no bbox; se não achar, usa a imagem toda
            crop = crop_bbox(img_bgr, bbox) if bbox is not None else img_bgr.copy()

            # Recorte "interno" — remove bordas/moldura da placa antes do OCR
            ocr_input = inner_crop(crop, ratio=0.08)

            # Best-plate tenta OCR + seleção do melhor candidato textual
            # Retorna (plate_text, confidence, candidates_list)
            p_prev, c_prev, cands_prev = best_plate(ocr_input)

            # Mostra amostras dos candidatos
            st.write(f"**Candidatos OCR (topo):** {cands_prev[:5]}")

            # Desenha o bbox + texto na imagem para visualização
            det_prev = annotate(img_bgr, bbox, p_prev or "")
            st.image(bgr2rgb(det_prev), caption="Detecção + texto (pré-processo)", width="stretch")

            # Mostra o crop que está sendo alimentado no OCR
            st.image(bgr2rgb(ocr_input), caption="Recorte usado no OCR (pré-processo)", width="stretch")
        # ---------- fim painel PDI ----------

        # Botão principal: dispara o pipeline completo e PERSISTE (salva no banco)
        if st.button("Processar"):
            # Salva uma cópia do upload (uma vez por conteúdo) e processa via pipeline unificada
            tmp_path = save_upload_once(img_bgr, st.session_state.upload_bytes)
            with st.spinner("Processando..."):
                res = process_image(str(tmp_path))  # roda todo o fluxo: detectar → recortar → OCR → salvar

            # Exibe resumo da leitura (placa, confiança, id)
            st.success(f"Placa: {res['plate_text'] or '(sem leitura)'} | confiança: {res['confidence']:.2f} | id={res['id']}")

            # Se a pipeline salvou arquivos (anotada/crop), mostramos ao usuário
            if res.get("annotated_path") and os.path.exists(res["annotated_path"]):
                st.image(res["annotated_path"], caption="Imagem anotada", width="stretch")
            if res.get("crop_path") and os.path.exists(res["crop_path"]):
                st.image(res["crop_path"], caption="Recorte utilizado no OCR", width="stretch")

# ---------------------------
# TAB 2 — Consultar registros
# ---------------------------
with tab2:
    st.subheader("Consultar registros")

    # Filtros básicos: parte do texto da placa e intervalo de datas
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        # Normalizamos para maiúsculas e sem espaços sobrando
        plate_filter = st.text_input("Placa contém", "").upper().strip()
    with col2:
        # Data inicial (default = primeiro dia do mês atual)
        dfrom = st.date_input("De", value=date.today().replace(day=1))
    with col3:
        # Data final (default = hoje)
        dto = st.date_input("Até", value=date.today())

    # Opção de agrupar: mostrar só o registro mais recente por placa
    group_latest = st.checkbox("Agrupar por placa (mostrar só o mais recente)", value=False)

    # Dispara a busca no banco quando clicar
    if st.button("Buscar"):
        s = SessionLocal()  # abre sessão de banco
        try:
            q = s.query(AccessRecord)  # query base

            # Filtro por placa (LIKE %texto%)
            if plate_filter:
                q = q.filter(AccessRecord.plate_text.like(f"%{plate_filter}%"))

            # Converte datas de UI para datetime (começo/fim do dia)
            dfrom_dt = datetime.combine(dfrom, datetime.min.time())  # 00:00:00
            dto_dt = datetime.combine(dto, datetime.max.time())      # 23:59:59.999999

            # Filtros de intervalo de data/hora
            q = q.filter(AccessRecord.created_at >= dfrom_dt)
            q = q.filter(AccessRecord.created_at <= dto_dt)

            # Ordena por ID (mais recente primeiro) e limita a 400 registros
            rows = q.order_by(AccessRecord.id.desc()).limit(400).all()
        finally:
            # Fecha a sessão SEMPRE (mesmo se der erro acima)
            s.close()

        # Agrupamento opcional: mantém apenas o registro mais recente por placa
        if group_latest:
            latest = {}
            for r in rows:
                key = (r.plate_text or "(sem)")
                # Se não existe ainda ou este é mais novo, substitui
                if key not in latest or r.created_at > latest[key].created_at:
                    latest[key] = r
            rows = list(latest.values())

        # Renderização: mensagem de vazio ou lista de cards com imagens
        if not rows:
            st.info("Nenhum registro encontrado para o filtro informado.")
        else:
            for r in rows:
                # Um "card" por registro
                with st.container(border=True):
                    # Cabeçalho do card: id, placa, confiança, timestamp
                    st.write(
                        f"**#{r.id}** — **{r.plate_text or '(sem leitura)'}** "
                        f"(conf.={r.confidence:.2f}) — {r.created_at:%Y-%m-%d %H:%M}"
                    )
                    # Duas colunas para mostrar imagens (se existirem no disco)
                    cols = st.columns(2)
                    if r.annotated_path and os.path.exists(r.annotated_path):
                        cols[0].image(r.annotated_path, caption="Anotada", width="stretch")
                    if r.plate_crop_path and os.path.exists(r.plate_crop_path):
                        cols[1].image(r.plate_crop_path, caption="Recorte", width="stretch")
