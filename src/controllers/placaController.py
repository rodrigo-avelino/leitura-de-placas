# src/controllers/placaController.py
import cv2
import numpy as np
from io import BytesIO, BufferedReader
from pathlib import Path
from datetime import datetime
from typing import Any

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

# (opcional) mantém diretórios se sua Persistencia salvar arquivos em disco
BASE_DIR = Path(__file__).resolve().parent.parent
ANNOTATED_DIR = BASE_DIR / "static" / "annotated"
CROP_DIR = BASE_DIR / "static" / "crops"
for d in [ANNOTATED_DIR, CROP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def _overlay_contours(bgr, contours, color=(0,255,255), thickness=2):
    if contours is None:
        return None
    out = bgr.copy()
    try:
        cv2.drawContours(out, contours, -1, color, thickness)
    except Exception:
        pass
    return out

def _overlay_quad(bgr, quad, color=(0,255,0), thickness=2):
    if quad is None:
        return None
    out = bgr.copy()
    q = np.asarray(quad).astype(int)
    pts = q.reshape((-1,1,2))
    cv2.polylines(out, [pts], isClosed=True, color=color, thickness=thickness)
    return out

def _read_image_bgr(source: Any) -> np.ndarray:
    """
    Aceita: path str/Path, bytes, BytesIO, UploadedFile (Streamlit), numpy.ndarray (BGR/RGB/GRAY), PIL.Image.
    Retorna: np.ndarray em BGR.
    """
    # numpy direto
    if isinstance(source, np.ndarray):
        img = source
        # se for RGB, converte pra BGR pra consistência
        if img.ndim == 3 and img.shape[2] == 3:
            # heurística: não há flag segura, mas se vier como RGB e o pipeline assume BGR, converta
            # (se já estiver em BGR, a diferença visual não afeta a detecção; melhor padronizar)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return img

    # UploadedFile do Streamlit
    if hasattr(source, "getbuffer"):  # st.uploaded_file
        data = source.getbuffer()
        n = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(n, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Falha ao decodificar a imagem enviada.")
        return img

    # BytesIO / BufferedReader
    if isinstance(source, (BytesIO, BufferedReader)):
        raw = source.read()
        n = np.frombuffer(raw, dtype=np.uint8)
        img = cv2.imdecode(n, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Falha ao decodificar a imagem (BytesIO).")
        return img

    # bytes puros
    if isinstance(source, (bytes, bytearray, memoryview)):
        n = np.frombuffer(source, dtype=np.uint8)
        img = cv2.imdecode(n, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Falha ao decodificar a imagem (bytes).")
        return img

    # PIL.Image
    try:
        from PIL import Image
        if isinstance(source, Image.Image):
            rgb = np.array(source.convert("RGB"))
            return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    except Exception:
        pass

    # path str/Path
    if isinstance(source, (str, Path)):
        p = Path(source)
        if not p.exists():
            raise FileNotFoundError(f"Imagem {p} não encontrada")
        img = cv2.imread(str(p), cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Falha ao ler a imagem em {p}")
        return img

    raise TypeError("Tipo de fonte de imagem não suportado para _read_image_bgr().")

class PlacaController:

    @staticmethod
    def processarImagem(source_image: Any, data_capturada: datetime, on_update=None):
        panel = {}

        def _emit(delta: dict):
            panel.update(delta)
            if on_update is not None:
                on_update(delta)

        # 1) Ler a imagem BGR
        img_bgr = _read_image_bgr(source_image)
        original = img_bgr.copy()

        # 2) Pré-processamento
        preproc = Preprocessamento.executar(img_bgr)
        _emit({"preproc": preproc})

        # 3) Bordas + Contornos
        edges = Bordas.executar(preproc)
        contours = Contornos.executar(edges)
        contours_overlay = _overlay_contours(original, contours)
        _emit({"contours_overlay": contours_overlay})

        # 4) Filtrar candidatos
        candidatos = FiltrarContornos.executar(contours, img_bgr)
        if not candidatos:
            return {
                "status": "erro",
                "texto_final": None,
                "panel": panel,
                "etapas": {"original": original, "preprocessamento": preproc, "bordas": edges, "contornos": contours, "candidatos": []},
            }

        best = candidatos[0]
        plate_bbox_overlay = _overlay_quad(original, best.get("quad"))
        _emit({"plate_bbox_overlay": plate_bbox_overlay})

        # 5) Recorte
        crop_rgb = Recorte.executar(img_bgr, best.get("quad"))
        _emit({"plate_crop": crop_rgb})

        # 6) Binarização
        bin_img = Binarizacao.executar(crop_rgb)
        _emit({"plate_binary": bin_img})

        # 7) Segmentação
        chars = Segmentacao.executar(bin_img)
        _emit({"chars": chars})

        # 8) OCR
        texto_raw = OCR.executarImg(crop_rgb)
        texto_chars = OCR.executarCaracteres(chars)
        ocr_text = (texto_raw or texto_chars or "").upper().strip()
        _emit({"ocr_text": ocr_text})

        # 9) Montagem
        plate_text = Montagem.executar(ocr_text)
        _emit({"plate_text": plate_text})

        # 10) Validação
        texto_final = Validacao.executar(plate_text)
        validation = {
            "válida": bool(texto_final),
            "entrada": plate_text,
            "saída": texto_final or "",
            "padrão": ("MERCOSUL" if texto_final and texto_final[4].isalpha() else "ANTIGA") if texto_final else "—"
        }
        _emit({"validation": validation})

        # 11) Persistência (se válido) — sem 'or' em arrays
        status = "ok" if texto_final else "invalido"
        persist_info = {}
        if texto_final:
            img_annot = plate_bbox_overlay if plate_bbox_overlay is not None else original
            Persistencia.salvar(
                texto_final,
                score=1.0,
                img_source=original,
                img_crop=crop_rgb,
                img_annot=img_annot,
                data_captura=data_capturada, 
            )
            persist_info = {"salvo": True, "placa": texto_final, "ts": data_capturada.isoformat()}
            _emit({"persist": persist_info})
        else:
            persist_info = {"salvo": False, "placa": "", "motivo": "validação falhou"}

        return {
            "status": status,
            "texto_final": texto_final,
            "panel": panel,
            "etapas": {
                "original": original,
                "preprocessamento": preproc,
                "bordas": edges,
                "contornos": contours,
                "candidatos": candidatos,
                "recorte": crop_rgb,
                "binarizacao": bin_img,
                "segmentacao": chars,
                "ocr_raw": texto_raw,
                "ocr_chars": texto_chars,
                "montagem": plate_text,
                "validacao": texto_final,
            },
        }

    @staticmethod
    def consultarRegistros(arg=None, data_inicio: datetime = None, data_fim: datetime = None):
        from src.config.db import SessionLocal
        from src.models.acessoModel import TabelaAcesso

        placa = None
        if isinstance(arg, dict):
            placa = arg.get("placa")
            data_inicio = arg.get("data_inicio", data_inicio)
            data_fim    = arg.get("data_fim", data_fim)
        else:
            placa = arg

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
            out = []
            for r in registros:
                out.append({
                    "placa": r.plate_text,
                    "score": r.confidence,
                    "caminho_origem": r.source_path,
                    "caminho_crop": r.plate_crop_path,
                    "caminho_annotated": r.annotated_path,
                    "data_hora": r.created_at.strftime("%d/%m/%Y %H:%M:%S"),
                })
            return out
        except Exception as e:
            print(f"[ERRO] Erro ao consultar registros: {e}")
            return []
        finally:
            db.close()