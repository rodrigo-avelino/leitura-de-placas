import cv2
from pathlib import Path
from datetime import datetime

from src.services.preprocessamento import Preprocessamento
from src.services.binarizacao import Binarizacao
from src.services.bordas import Bordas
from src.services.contornos import Contornos
from src.services.filtrarContornos import FiltrarContornos
from src.services.recorte import Recorte
from src.services.segmentacao import Segmentacao
from src.services.ocr import OCR
from src.services.montagem import Montagem
from src.services.validacao import Validacao
from src.services.persistencia import Persistencia

from src.config.db import SessionLocal
from src.models.acessoModel import TabelaAcesso


BASE_DIR = Path(__file__).resolve().parents[1]  # pasta backend
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
ANNOTATED_DIR = BASE_DIR / "static" / "annotated"
CROP_DIR = BASE_DIR / "static" / "crops"

for d in [UPLOAD_DIR, ANNOTATED_DIR, CROP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

print("📁 Diretório base:", BASE_DIR)
print("📂 Uploads:", UPLOAD_DIR)

for d in [UPLOAD_DIR, ANNOTATED_DIR, CROP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

class PlacaController:

    @staticmethod
    def processarImagem(nome_arquivo: str):
        caminho = UPLOAD_DIR / nome_arquivo
        if not caminho.exists():
            raise FileNotFoundError(f"Imagem {caminho} não encontrada")

        resultados = {}

        # 1) Carregar
        img_bgr = cv2.imread(str(caminho))
        # NÃO adicione imagens ao resultado que será retornado como JSON
        # resultados["original"] = img_bgr

        # 2) Pré-processamento
        img_prep = Preprocessamento.executar(img_bgr)
        # resultados["preprocessamento"] = img_prep

        # 3) Bordas
        img_bordas = Bordas.executar(img_prep)
        # resultados["bordas"] = img_bordas

        # 4) Contornos
        conts = Contornos.executar(img_bordas)
        resultados["num_contornos"] = len(conts)  # apenas números, não arrays

        # 5) Filtrar
        candidatos = FiltrarContornos.executar(conts, img_bgr)
        # Remover dados não serializáveis dos candidatos
        candidatos_json = []
        for c in candidatos:
            candidatos_json.append({
                "tipo": c.get("tipo"),
                "score": c.get("score"),
                "aspect_ratio": c.get("aspect_ratio"),
                "metodo": c.get("metodo")
            })
        resultados["candidatos"] = candidatos_json

        if not candidatos:
            return {"status": "erro", "mensagem": "Nenhuma placa encontrada", "etapas": resultados}

        # 6) Recorte
        best = candidatos[0]
        crop_rgb = Recorte.executar(img_bgr, best["quad"])
        # resultados["recorte"] = crop_rgb

        # 7) Binarização
        bin_img = Binarizacao.executar(crop_rgb)
        # resultados["binarizacao"] = bin_img

        # 8) Segmentação
        chars = Segmentacao.executar(bin_img)
        resultados["num_caracteres"] = len(chars)  # apenas contagem

        # 9) OCR (placa inteira + por caracteres)
        texto_raw = OCR.executarImg(crop_rgb)
        texto_chars = OCR.executarCaracteres(chars)
        resultados["ocr_raw"] = texto_raw
        resultados["ocr_chars"] = texto_chars

        # 10) Montagem
        texto_montado = Montagem.executar(texto_raw or texto_chars)
        resultados["montagem"] = texto_montado

        # 11) Validação
        texto_final = Validacao.executar(texto_montado)
        resultados["validacao"] = texto_final

        # 12) Persistência (se válido)
        if texto_final:
            Persistencia.salvar(
                texto_final,
                score=1.0,
                img_source=img_bgr,
                img_crop=crop_rgb,
                img_annot=img_bgr
            )
            status = "ok"
        else:
            status = "invalido"

        return {
            "status": status,
            "texto_final": texto_final,
            "etapas": resultados,
            "caminho_crop": str(CROP_DIR / f"crop_{nome_arquivo}"),
            "caminho_annotated": str(ANNOTATED_DIR / f"annotated_{nome_arquivo}")
        }

    @staticmethod
    def consultarRegistros(placa: str = None, data_inicio: datetime = None, data_fim: datetime = None):
        """
        Consulta registros no banco com filtros opcionais.
        - placa: busca por parte ou placa exata
        - data_inicio, data_fim: intervalo de datas
        """
        db = SessionLocal()
        try:
            query = db.query(TabelaAcesso)

            if placa:
                query = query.filter(TabelaAcesso.plate_text.ilike(f"%{placa}%"))

            if data_inicio:
                query = query.filter(TabelaAcesso.created_at >= data_inicio)

            if data_fim:
                query = query.filter(TabelaAcesso.created_at <= data_fim)

            registros = query.order_by(TabelaAcesso.created_at.desc()).all()

            resultados = []
            for r in registros:
                resultados.append({
                    "placa": r.plate_text,
                    "score": r.confidence,
                    "caminho_origem": r.source_path,
                    "caminho_crop": r.plate_crop_path,
                    "caminho_annotated": r.annotated_path,
                    "data_hora": r.created_at.strftime("%d/%m/%Y %H:%M:%S"),
                })

            return resultados

        except Exception as e:
            print(f"[ERRO] Erro ao consultar registros: {e}")
            return []
        finally:
            db.close()
