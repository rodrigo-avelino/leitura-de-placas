import streamlit as st

PDI_CSS = """
<style>
.pdi-card {
  border: 1px solid rgba(255,255,255,.12);
  background: #12161b;
  border-radius: 14px;
  padding: 18px;
  margin-top: 14px;
}
.pdi-title {
  display:flex; align-items:center; gap:10px;
  font-weight: 800; font-size: 1.2rem; color:#e9eef5; margin:0 0 12px 0;
}
.step {
  background:#181d23; border:1px solid rgba(255,255,255,.06);
  border-radius: 10px; padding:14px 16px; margin-bottom:12px;
}
.step-head { display:flex; align-items:center; gap:12px; }
.step-icon {
  width:40px; height:40px; border-radius:10px;
  background:#13181f; display:flex; align-items:center; justify-content:center;
  font-size:18px; color:#dfe7f2;
}
.step-text .t { color:#e9eef5; font-weight:700; line-height:1.2 }
.step-text .s { color:#a9b6c6; font-size:.92rem; margin-top:2px }
.crop {
  margin-top:12px;
  border:2px dashed rgba(255,255,255,.18);
  border-radius:10px;
  padding:14px;
  background:#0f1318;
}
.crop-label {
  color:#a9b6c6; font-size:.9rem; margin-bottom:6px;
}
.thumb-row { display:flex; flex-wrap:wrap; gap:10px; }
.thumb { border-radius:8px; overflow:hidden; }
</style>
"""

def _crop_image(img, caption=None, channels=None, clamp=False):
    """Renderiza uma imagem dentro do crop (se existir)."""
    if img is None:
        st.markdown('<div class="crop-label">🔸 Resultado não gerado para esta etapa.</div>', unsafe_allow_html=True)
        return
    st.markdown('', unsafe_allow_html=True)
    st.image(img, caption=caption, channels=channels, use_column_width=True, clamp=clamp)

def _crop_grid(images, titles=None, channels=None):
    if not images:
        st.markdown('<div class="crop-label">🔸 Nenhum candidato encontrado.</div>', unsafe_allow_html=True)
        return
    cols = st.columns(min(4, max(1, len(images))))
    for i, img in enumerate(images):
        with cols[i % len(cols)]:
            st.image(img, caption=titles[i] if titles and i < len(titles) else None,
                     channels=channels, use_column_width=True)

def painel_pdi(result: dict, expand: bool = True):
    """
    Renderiza o acordeão “Análise PDI” com um “crop” para cada etapa.
    Espera as chaves que seu backend já envia:
      - original, preprocessamento, bordas, recorte, binarizacao, segmentacao (lista)
    """
    st.markdown(PDI_CSS, unsafe_allow_html=True)
    with st.expander("🧠 Análise PDI (modo notebook)", expanded=expand):
        st.markdown('<div class="pdi-card">', unsafe_allow_html=True)

        # 1) Conversão Grayscale -> result["preprocessamento"]
        st.markdown("""
        <div class="step">
          <div class="step-head">
            <div class="step-icon">📷</div>
            <div class="step-text">
              <div class="t">1. Conversão Grayscale</div>
              <div class="s">Conversão para escala de cinza para reduzir complexidade</div>
            </div>
          </div>
          <div class="crop">
        """, unsafe_allow_html=True)
        _crop_image(result.get("preprocessamento"), caption="Grayscale / Pré-processamento", channels="GRAY")
        st.markdown("</div></div>", unsafe_allow_html=True)

        # 2) Análise de Histograma (placeholder por enquanto)
        st.markdown("""
        <div class="step">
          <div class="step-head">
            <div class="step-icon">📊</div>
            <div class="step-text">
              <div class="t">2. Análise de Histograma</div>
              <div class="s">Análise da distribuição de intensidades</div>
            </div>
          </div>
          <div class="crop">
        """, unsafe_allow_html=True)
        # se futuramente você gerar uma imagem de histograma, passe aqui
        _crop_image(result.get("histograma"), caption="Histograma (quando disponível)")
        st.markdown("</div></div>", unsafe_allow_html=True)

        # 3) Equalização + CLAHE (placeholder)
        st.markdown("""
        <div class="step">
          <div class="step-head">
            <div class="step-icon">✨</div>
            <div class="step-text">
              <div class="t">3. Equalização + CLAHE</div>
              <div class="s">Melhoria de contraste adaptativo</div>
            </div>
          </div>
          <div class="crop">
        """, unsafe_allow_html=True)
        _crop_image(result.get("clahe"), caption="CLAHE (quando disponível)", channels="GRAY")
        st.markdown("</div></div>", unsafe_allow_html=True)

        # 4) Detecção de Placa -> result["bordas"] (ou anotada quando você tiver)
        st.markdown("""
        <div class="step">
          <div class="step-head">
            <div class="step-icon">🔍</div>
            <div class="step-text">
              <div class="t">4. Detecção de Placa</div>
              <div class="s">Identificação da região da placa veicular</div>
            </div>
          </div>
          <div class="crop">
        """, unsafe_allow_html=True)
        _crop_image(result.get("bordas"), caption="Bordas (Canny)", channels="GRAY")
        st.markdown("</div></div>", unsafe_allow_html=True)

        # 5) Crop & Candidatos -> result["recorte"] e result["segmentacao"]
        st.markdown("""
        <div class="step">
          <div class="step-head">
            <div class="step-icon">🧩</div>
            <div class="step-text">
              <div class="t">5. Crop &amp; Candidatos</div>
              <div class="s">Extração e análise de caracteres candidatos</div>
            </div>
          </div>
          <div class="crop">
        """, unsafe_allow_html=True)
        _crop_image(result.get("recorte"), caption="Recorte da Placa", channels="BGR")
        seg = result.get("segmentacao") or []
        if seg:
            st.markdown('<div class="crop-label">Caracteres segmentados</div>', unsafe_allow_html=True)
            _crop_grid(seg, titles=[f"Char {i+1}" for i in range(len(seg))], channels="GRAY")
        st.markdown("</div></div>", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
