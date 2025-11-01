import cv2
from pathlib import Path
from datetime import datetime

from ..services.preprocessamento import Preprocessamento
from ..services.binarizacao import Binarizacao
from ..services.bordas import Bordas
from ..services.contornos import Contornos
from ..services.filtrarContornos import FiltrarContornos
from ..services.recorte import Recorte
from ..services.segmentacao import Segmentacao
from ..services.ocr import OCR
from ..services.montagem import Montagem
from ..services.validacao import Validacao
from ..services.persistencia import Persistencia

BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
ANNOTATED_DIR = BASE_DIR / "static" / "annotated"
CROP_DIR = BASE_DIR / "static" / "crops"

for d in [UPLOAD_DIR, ANNOTATED_DIR, CROP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

print("📁 Diretório base:", BASE_DIR)
print("📂 Uploads:", UPLOAD_DIR)

class PlacaController:
    @staticmethod
    def processarImagem(nome_arquivo: str):
        caminho = UPLOAD_DIR / nome_arquivo
        if not caminho.exists():
            raise FileNotFoundError(f"Imagem {caminho} não encontrada")

        resultados = {}

        # 1) Carregar imagem
        img_bgr = cv2.imread(str(caminho))

        # 2) Pré-processamento
        img_prep = Preprocessamento.executar(img_bgr)

        # 3) Bordas
        img_bordas = Bordas.executar(img_prep)

        # 4) Contornos
        conts = Contornos.executar(img_bordas)
        resultados["num_contornos"] = len(conts)

        # 5) Filtrar contornos candidatos
        candidatos = FiltrarContornos.executar(conts, img_bgr)
        candidatos_json = [
            {
                "tipo": c.get("tipo"),
                "score": c.get("score"),
                "aspect_ratio": c.get("aspect_ratio"),
                "metodo": c.get("metodo"),
            }
            for c in candidatos
        ]
        resultados["candidatos"] = candidatos_json

        if not candidatos:
            return {"status": "erro", "mensagem": "Nenhuma placa encontrada", "etapas": resultados}

        # 6) Recorte
        best = candidatos[0]
        crop_rgb = Recorte.executar(img_bgr, best["quad"])

        # 7) Binarização
        bin_img = Binarizacao.executar(crop_rgb)

        # 8) Segmentação
        chars = Segmentacao.executar(bin_img)
        resultados["num_caracteres"] = len(chars)

        # 9) OCR
        texto_raw, _ = OCR.executarImg(crop_rgb)
        texto_chars = OCR.executarCaracteres(chars)
        resultados["ocr_raw"] = texto_raw
        resultados["ocr_chars"] = texto_chars

        # 10) Montagem
        texto_montado = Montagem.executar(texto_raw or texto_chars)
        resultados["montagem"] = texto_montado

        # 11) Validação
        texto_final = Validacao.executar(texto_montado)
        resultados["validacao"] = texto_final

        # 12) Persistência
        status = "ok" if texto_final else "invalido"
        if texto_final:
            Persistencia.salvar(
                texto_final,
                score=1.0,
                img_source=img_bgr,
                img_crop=crop_rgb,
                img_annot=img_bgr
            )

        return {
            "status": status,
            "texto_final": texto_final,
            "etapas": resultados,
            "caminho_crop": str(CROP_DIR / f"crop_{nome_arquivo}"),
            "caminho_annotated": str(ANNOTATED_DIR / f"annotated_{nome_arquivo}")
        }
