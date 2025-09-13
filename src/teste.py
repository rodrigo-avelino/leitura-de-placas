import cv2
import matplotlib.pyplot as plt
from pathlib import Path

from services.filtrarContornos import FiltrarContornos
from services.binarizacao import Binarizacao
from services.segmentacao import Segmentacao
from services.ocr import OCR
from services.montagem import Montagem
from services.validacao import Validacao
from services.persistencia import Persistencia


from config.db import UPLOAD_DIR, CROP_DIR, ANNOTATED_DIR

NOME_IMAGEM = "teste8.png"

# Diretórios
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
ANNOTATED_DIR = BASE_DIR / "static" / "annotated"
CROP_DIR = BASE_DIR / "static" / "crops"

for d in [ANNOTATED_DIR, CROP_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def processar_imagem(nome_arquivo):
    caminho = UPLOAD_DIR / nome_arquivo
    if not caminho.exists():
        raise FileNotFoundError(f"Imagem não encontrada: {caminho}")

    img_bgr = cv2.imread(str(caminho))
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 100, 200)

    contornos, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    candidatos = FiltrarContornos.executar(contornos, img_bgr)

    annotated = img_rgb.copy()
    crop = None
    if candidatos:
        best = candidatos[0]
        x, y, w, h = best["box"]
        quad = best["quad"].astype(int)

        # desenha bounding box
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 3)
        # desenha quadrilátero
        cv2.polylines(annotated, [quad], True, (255, 0, 0), 2)

        # recorte simples (bbox)
        crop = img_rgb[y:y+h, x:x+w]

        # ---- salvar ----
        out_annot = ANNOTATED_DIR / f"annotated_{nome_arquivo}"
        out_crop = CROP_DIR / f"crop_{nome_arquivo}"
        cv2.imwrite(str(out_annot), cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR))
        cv2.imwrite(str(out_crop), cv2.cvtColor(crop, cv2.COLOR_RGB2BGR))
        print(f"[OK] Resultados salvos:\n - {out_annot}\n - {out_crop}")
    else:
        print("[ERRO] Nenhum candidato encontrado.")

    # ---- Mostrar resultados ----
    fig, axs = plt.subplots(1, 3, figsize=(20, 8))
    axs[0].imshow(img_rgb); axs[0].set_title("Original"); axs[0].axis("off")
    axs[1].imshow(edges, cmap="gray"); axs[1].set_title("Bordas (Canny)"); axs[1].axis("off")
    axs[2].imshow(annotated); axs[2].set_title("Candidato"); axs[2].axis("off")
    plt.show()

    if crop is not None:
        plt.figure(figsize=(6, 3))
        plt.imshow(crop)
        plt.title("Recorte da Placa")
        plt.axis("off")
        plt.show()

        # NOVO: OCR completo
        executar_pipeline_ocr(crop, nome_arquivo)

def executar_pipeline_ocr(crop_rgb, nome_arquivo):
    print(f"\n[INFO] Iniciando OCR para {nome_arquivo}...")

    bin_img = Binarizacao.executar(crop_rgb, metodo='adaptive_gaussian', invertido=True)
    texto_raw = OCR.executarImg(crop_rgb)
    print(f"[OCR - Imagem Inteira] Texto bruto: {texto_raw}")

    caracteres = Segmentacao.executar(bin_img)
    texto_segmentado = OCR.executarCaracteres(caracteres) if caracteres else ""

    for texto in [texto_raw, texto_segmentado]:
        texto_corrigido = Montagem.executar(texto)
        print(f"[DEBUG] Tentando validar: {texto_corrigido}")
        placa_validada = Validacao.executar(texto_corrigido)

        if placa_validada:
            # Calcular "confiança" com base simples (você pode melhorar isso depois)
            score = 0.9 if texto == texto_raw else 0.6

            Persistencia.salvar(
                placa=placa_validada,
                score=score,
                caminho_origem=UPLOAD_DIR / nome_arquivo,
                caminho_crop=CROP_DIR / f"crop_{nome_arquivo}",
                caminho_annot=ANNOTATED_DIR / f"annotated_{nome_arquivo}"
            )
            return placa_validada

    print("[FALHA] Nenhuma placa válida foi reconhecida.")
    return None

if __name__ == "__main__":
    processar_imagem(NOME_IMAGEM)
