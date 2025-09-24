import cv2
import numpy as np
import streamlit as st
from typing import Any, Dict, List, Sequence

# ... (As funções cropImage e cropGrid permanecem as mesmas de antes) ...
def cropImage(img: Any, caption: str | None = None, channels: str | None = None, clamp: bool = False) -> None:
    if img is None:
        st.markdown('<div class="crop-label">Nenhum resultado nesta etapa.</div>', unsafe_allow_html=True)
        return
    if isinstance(img, np.ndarray) and img.size == 0:
        st.markdown('<div class="crop-label">Nenhum resultado nesta etapa.</div>', unsafe_allow_html=True)
        return
    st.image(img, caption=caption, channels=channels, width=400, clamp=clamp)

def cropGrid(images: Any, titles: Sequence[str] | None = None, channels: str | None = None) -> None:
    if images is None:
        st.markdown('<div class="crop-label">Nenhum candidato encontrado.</div>', unsafe_allow_html=True)
        return
    if isinstance(images, np.ndarray):
        images = [images]
    elif not isinstance(images, (list, tuple)):
        images = [images]
    cleaned: List[Any] = []
    for im in images:
        if im is None: continue
        if isinstance(im, np.ndarray) and im.size == 0: continue
        cleaned.append(im)
    if len(cleaned) == 0:
        st.markdown('<div class="crop-label">Nenhum candidato encontrado.</div>', unsafe_allow_html=True)
        return
    ncols = min(7, max(1, len(cleaned)))
    cols = st.columns(ncols)
    for i, im in enumerate(cleaned):
        with cols[i % ncols]:
            resized_im = cv2.resize(im, (96, 192), interpolation=cv2.INTER_NEAREST)
            st.image(
                resized_im,
                caption=(titles[i] if titles and i < len(titles) else None),
                channels=channels,
            )

# ... (A variável PDI_CSS permanece a mesma) ...
PDI_CSS = """
<style>
  /* ... (COLE TODO O BLOCO CSS DA VERSÃO ANTERIOR AQUI) ... */
  /* ========= tokens do painel ========= */
  :root {
    --pdi-bg:        #0f141a;
    --pdi-card:      #181e26;
    --pdi-inner:     #10151b;
    --pdi-stroke:    rgba(255,255,255,.10);
    --pdi-stroke-2:  rgba(255,255,255,.18);
    --pdi-dash:      rgba(255,255,255,.16);
    --pdi-text:      #e9eef5;
    --pdi-sub:       #a9b6c6;
    --pdi-accent:    #60a5fa;  /* azul */
    --pdi-accent-2:  #34d399;  /* verde */
    --pdi-shadow:    0 8px 20px rgba(0,0,0,.35);
  }
  .pdi-title { font-size: 1.18rem; font-weight: 800; color: var(--pdi-text); margin: 2px 2px 14px 2px; letter-spacing: .2px; }
  .pdi-exp { position: relative; }
  .pdi-exp [data-testid="stExpander"] > details { background: var(--pdi-card); border: 1px solid var(--pdi-stroke); border-radius: 14px; padding: 0; margin-bottom: 12px; box-shadow: var(--pdi-shadow); transition: border-color .18s ease, transform .12s ease, box-shadow .18s ease; }
  .pdi-exp [data-testid="stExpander"] > details:hover { border-color: var(--pdi-stroke-2); transform: translateY(-1px); box-shadow: 0 12px 26px rgba(0,0,0,.40); }
  .pdi-exp [data-testid="stExpander"] > details > summary { list-style: none; display: flex; align-items: center; gap: 12px; padding: 14px 16px; cursor: pointer; user-select: none; outline: none; color: var(--pdi-text); font-weight: 700; }
  .pdi-exp [data-testid="stExpander"] > details > summary::-webkit-details-marker { display: none; }
  .pdi-exp [data-testid="stExpander"] > details > summary::after { content: "›"; margin-left: auto; font-size: 18px; line-height: 1; transform: rotate(0deg); transition: transform .18s ease; color: var(--pdi-sub); }
  .pdi-exp [data-testid="stExpander"] > details[open] > summary::after { transform: rotate(90deg); color: var(--pdi-accent); }
  .pdi-exp [data-testid="stExpander"] > details > summary .badge-step { display: inline-flex; align-items: center; justify-content: center; min-width: 24px; height: 24px; padding: 0 8px; font-size: .82rem; font-weight: 800; background: rgba(96,165,250,.12); color: var(--pdi-accent); border: 1px solid rgba(96,165,250,.35); border-radius: 999px; }
  .pdi-exp [data-testid="stExpander"] > details > summary .sub { font-weight: 500; color: var(--pdi-sub); font-size: .92rem; }
  .pdi-exp [data-testid="stExpander"] > details[open] > div { margin: 0 0 12px 0; padding: 12px 14px 16px 14px; background: var(--pdi-inner); border-radius: 0 0 14px 14px; }
  .step-title { font-weight: 700; color: var(--pdi-text); }
  .step-sub   { font-size: .92rem; color: var(--pdi-sub); margin: 6px 0 8px; }
  .crop { margin-top: 8px; background: var(--pdi-bg); border-radius: 12px; padding: 12px; transition: border-color .18s ease, background .18s ease; }
  .crop:hover { border-color: var(--pdi-stroke-2); background: #0d1217; }
  .crop-label { color: var(--pdi-sub); font-size: .9rem; }
  .kv { display: grid; grid-template-columns: 172px 1fr; gap: 8px 12px; margin-top: 8px; }
  .kv div:first-child { color: var(--pdi-sub); }
  .ocr-text { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 1rem; padding: 8px 10px; border-radius: 10px; background: var(--pdi-bg); border: 1px solid var(--pdi-stroke-2); color: var(--pdi-text); display: inline-block; }
  .pdi-exp .stImage img { border-radius: 10px; }
  @media (max-width: 680px) {
    .pdi-title { font-size: 1.08rem; }
    .kv { grid-template-columns: 130px 1fr; }
  }
</style>
"""

# ... (A variável MAIN_STEPS e as funções _is_empty, _pick_value, _render permanecem as mesmas) ...
MAIN_STEPS: List[Dict[str, Any]] = [
    {"title":"Pré-processamento", "sub":"Conversão para cinza e suavização.", "keys":["preproc","preprocessamento","gauss"], "kind":"image", "channels":"GRAY"},
    {"title":"Bordas e Contornos", "sub":"Regiões candidatas destacadas.", "keys":["contours_overlay","edges_overlay","bordas"], "kind":"image", "channels":"BGR"},
    {"title":"Detecção da Placa", "sub":"Placa localizada na imagem.", "keys":["plate_bbox_overlay"], "kind":"image", "channels":"BGR"},
    {"title":"Recorte da Placa", "sub":"Crop da região estimada.", "keys":["plate_crop","recorte"], "kind":"image", "channels":"BGR"},
    {"title":"Binarização", "sub":"Separação foreground/background para OCR.", "keys":["plate_binary","binarizacao"], "kind":"image", "channels":"GRAY"},
    {"title":"Caracteres Segmentados", "sub":"Candidatos identificados (ordem de leitura).", "keys":["chars","segmentacao"], "kind":"grid", "channels":"GRAY"},
    {"title":"OCR", "sub":"Leitura dos caracteres.", "keys":["ocr_text"], "kind":"text"},
    {"title":"Validação e Armazenamento", "sub":"Padrão, consistência e registro.", "keys":["validation"], "kind":"kv"},
]

def _is_empty(v: Any) -> bool:
    if v is None: return True
    if isinstance(v, str): return len(v.strip()) == 0
    if isinstance(v, (list, tuple, set, dict)): return len(v) == 0
    if isinstance(v, np.ndarray): return v.size == 0
    return False

def _pick_value(result: dict, keys: List[str]):
    for k in keys:
        if k in result:
            v = result[k]
            # --- MODIFICAÇÃO IMPORTANTE ---
            # Se a chave for 'binarizacao', pegamos o resultado final do dicionário
            if k == 'binarizacao' and isinstance(v, dict):
                return v.get('resultado_final')
            if not _is_empty(v): return v
    
    # Fallback para o caso de 'binarizacao'
    v = result.get('binarizacao')
    if isinstance(v, dict):
        return v.get('resultado_final')
        
    return result.get(keys[0])

def _render(kind: str, value: Any, channels=None):
    if kind == "image": cropImage(value, channels=channels)
    elif kind == "grid": cropGrid(value, channels=channels)
    elif kind == "text":
        if _is_empty(value): st.markdown('<div class="crop-label">Sem texto disponível.</div>', unsafe_allow_html=True)
        else: st.markdown(f'<span class="ocr-text">{value}</span>', unsafe_allow_html=True)
    elif kind == "kv":
        data = value if isinstance(value, dict) else {}
        if _is_empty(data): st.markdown('<div class="crop-label">Sem dados.</div>', unsafe_allow_html=True)
        else:
            rows = "".join([f"<div>{k}</div><div>{v}</div>" for k, v in data.items()])
            st.markdown(f'<div class="kv">{rows}</div>', unsafe_allow_html=True)

def panelPDI(result: dict, show_tech: bool | None = None, key: str = "pdi"):
    st.markdown(PDI_CSS, unsafe_allow_html=True)
    st.markdown('<div class="pdi-exp">', unsafe_allow_html=True)
    st.markdown('<div class="pdi-title">Análise de Processamento Digital de Imagem</div>', unsafe_allow_html=True)

    for idx, step in enumerate(MAIN_STEPS, 1):
        with st.expander(f"{idx}. {step['title']}"):
            st.markdown(f'<div class="step-title">{step["title"]}</div>', unsafe_allow_html=True)
            if step.get("sub"): st.markdown(f'<div class="step-sub">{step["sub"]}</div>', unsafe_allow_html=True)
            st.markdown('<div class="crop">', unsafe_allow_html=True)
            value = _pick_value(result or {}, step["keys"])
            _render(step["kind"], value, channels=step.get("channels"))
            st.markdown('</div>', unsafe_allow_html=True)

    # --- NOVO PAINEL DE DEPURAÇÃO DE BINARIZAÇÃO ---
    bin_debug_info = result.get("binarizacao", {}).get("debug_candidatos") if isinstance(result.get("binarizacao"), dict) else None
    if bin_debug_info:
        with st.expander("🕵️ Debug Binarização"):
            st.markdown('<div class="step-title">Análise dos Candidatos de Binarização</div>', unsafe_allow_html=True)
            st.markdown('<div class="step-sub">Resultado de cada técnica e sua respectiva nota (score).</div>', unsafe_allow_html=True)
            for cand in bin_debug_info:
                st.markdown(f"--- \n **Técnica:** `{cand['nome']}` | **Score:** `{cand['score']:.3f}`")
                st.image(cand['imagem'], channels="GRAY", width=400)

    st.markdown('</div>', unsafe_allow_html=True)