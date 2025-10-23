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

# Nome do arquivo a ser processado quando rodar diretamente este script
NOME_IMAGEM = "teste8.png"

# --- Definição/garantia de diretórios de saída locais (caso não venham do config) ---
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
ANNOTATED_DIR = BASE_DIR / "static" / "annotated"
CROP_DIR = BASE_DIR / "static" / "crops"

# Cria pastas de saída se ainda não existirem
for d in [ANNOTATED_DIR, CROP_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def processar_imagem(nome_arquivo):
    """
    Pipeline visual "rápido" para:
      1) Ler a imagem do disco
      2) Extrair bordas (Canny) e contornos
      3) Filtrar contornos candidatos a placa (FiltrarContornos)
      4) Desenhar anotações (bbox e quadrilátero) + salvar imagens
      5) Exibir figuras (original, bordas, anotada)
      6) Se houver recorte de placa, aciona o pipeline de OCR completo
    """
    caminho = UPLOAD_DIR / nome_arquivo
    if not caminho.exists():
        raise FileNotFoundError(f"Imagem não encontrada: {caminho}")

    # Lê em BGR (padrão OpenCV) e converte uma cópia para RGB para exibição no matplotlib
    img_bgr = cv2.imread(str(caminho))
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # Pré-processo básico para detecção de bordas: cinza + blur + Canny
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 100, 200)

    # Localiza contornos nas bordas
    contornos, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Heurística de filtragem/priorização dos contornos candidatos a placa
    candidatos = FiltrarContornos.executar(contornos, img_bgr)

    # Cópia para desenhar anotações; crop começa vazio
    annotated = img_rgb.copy()
    crop = None

    if candidatos:
        # Usa o primeiro candidato (lista já vem ordenada por score decrescente)
        best = candidatos[0]
        x, y, w, h = best["box"]
        quad = best["quad"].astype(int)

        # Desenha retângulo "bounding box" do candidato
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 3)
        # Desenha o quadrilátero refinado (mais preciso na placa)
        cv2.polylines(annotated, [quad], True, (255, 0, 0), 2)

        # Recorte simples usando a bbox (rápido; o warp por quadrilátero poderia ser usado também)
        crop = img_rgb[y:y+h, x:x+w]

        # --- Persistência de imagens de saída (apenas arquivos, sem banco aqui) ---
        out_annot = ANNOTATED_DIR / f"annotated_{nome_arquivo}"
        out_crop = CROP_DIR / f"crop_{nome_arquivo}"
        # Converte de volta para BGR antes de salvar com OpenCV
        cv2.imwrite(str(out_annot), cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR))
        cv2.imwrite(str(out_crop), cv2.cvtColor(crop, cv2.COLOR_RGB2BGR))
        print(f"[OK] Resultados salvos:\n - {out_annot}\n - {out_crop}")
    else:
        print("[ERRO] Nenhum candidato encontrado.")

    # --- Visualização rápida no matplotlib (para debug ou relatório) ---
    fig, axs = plt.subplots(1, 3, figsize=(20, 8))
    axs[0].imshow(img_rgb);  axs[0].set_title("Original");         axs[0].axis("off")
    axs[1].imshow(edges, cmap="gray"); axs[1].set_title("Bordas (Canny)"); axs[1].axis("off")
    axs[2].imshow(annotated); axs[2].set_title("Candidato");       axs[2].axis("off")
    plt.show()

    # Se houve recorte, aciona pipeline de OCR + validação + persistência no banco
    if crop is not None:
        plt.figure(figsize=(6, 3))
        plt.imshow(crop)
        plt.title("Recorte da Placa")
        plt.axis("off")
        plt.show()

        # Executa OCR completo (binarização, segmentação, correspondência, validação e salvar no banco)
        executar_pipeline_ocr(crop, nome_arquivo)


def executar_pipeline_ocr(crop_rgb, nome_arquivo):
    """
    Pipeline de reconhecimento:
      1) Binariza o recorte (adaptive_gaussian invertido)
      2) OCR do recorte inteiro
      3) Segmenta possíveis caracteres e tenta OCR por caractere
      4) Monta e valida candidatos, persistindo o primeiro válido no banco
    """
    print(f"\n[INFO] Iniciando OCR para {nome_arquivo}...")

    # Binarização indicada para placas (destaca texto); retorna imagem binária
    bin_img = Binarizacao.executar(crop_rgb, metodo='adaptive_gaussian', invertido=True)

    # OCR direto do recorte (imagem colorida)
    texto_raw = OCR.executarImg(crop_rgb)
    print(f"[OCR - Imagem Inteira] Texto bruto: {texto_raw}")

    # Segmenta caracteres a partir da binarizada
    caracteres = Segmentacao.executar(bin_img)

    # OCR por caractere segmentado (normalmente ajuda em casos com ruído)
    texto_segmentado = OCR.executarCaracteres(caracteres) if caracteres else ""

    # Tenta validar em duas ordens: primeiro o texto da imagem inteira, depois o segmentado
    for texto in [texto_raw, texto_segmentado]:
        # "Montagem" = normalização/ajustes básicos (ex.: remover separadores, unir tokens etc.)
        texto_corrigido = Montagem.executar(texto)
        print(f"[DEBUG] Tentando validar: {texto_corrigido}")

        # Validação final contra os padrões de placa (ABC1234 / ABC1D23), com correções posicional/ambíguas
        placa_validada = Validacao.executar(texto_corrigido)

        if placa_validada:
            # Score simples (heurístico): dá mais peso ao OCR do recorte inteiro
            score = 0.9 if texto == texto_raw else 0.6

            # Persiste no banco este resultado (imagens em disco já foram salvas na etapa anterior)
            Persistencia.salvar(
                placa=placa_validada,
                score=score,
                caminho_origem=UPLOAD_DIR / nome_arquivo,
                caminho_crop=CROP_DIR / f"crop_{nome_arquivo}",
                caminho_annot=ANNOTATED_DIR / f"annotated_{nome_arquivo}"
            )
            return placa_validada

    # Se nenhum texto passou na validação, informa falha
    print("[FALHA] Nenhuma placa válida foi reconhecida.")
    return None


# Execução direta do módulo (ex.: `python este_arquivo.py`)
if __name__ == "__main__":
    processar_imagem(NOME_IMAGEM)
