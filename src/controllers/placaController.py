import cv2
import base64
import numpy as np
from typing import Any
from pathlib import Path
from io import BytesIO, BufferedReader
from datetime import datetime, timedelta

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

from src.models.acessoModel import TabelaAcesso
from src.config.db import SessionLocal

# (opcional) mantém diretórios se sua Persistencia salvar arquivos em disco
BASE_DIR = Path(__file__).resolve().parent.parent
ANNOTATED_DIR = BASE_DIR / "static" / "annotated"
CROP_DIR = BASE_DIR / "static" / "crops"
for d in [ANNOTATED_DIR, CROP_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def _overlay_contours(bgr, contours, color=(0, 255, 255), thickness=2):
    if contours is None:
        return None
    out = bgr.copy()
    try:
        cv2.drawContours(out, contours, -1, color, thickness)
    except Exception:
        pass
    return out


def _overlay_quad(bgr, quad, color=(0, 255, 0), thickness=2):
    if quad is None:
        return None
    out = bgr.copy()
    q = np.asarray(quad).astype(int)
    pts = q.reshape((-1, 1, 2))
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
        # leitura robusta para caminhos com acentos/onedrive
        data = np.fromfile(str(p), dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Falha ao ler a imagem em {p}")
        return img

    raise TypeError("Tipo de fonte de imagem não suportado para _read_image_bgr().")


class PlacaController:

   # Dentro da classe PlacaController
    @staticmethod
    def processarImagem(source_image: Any, data_capturada: datetime, on_update=None):
        panel = {}
        def _emit(delta: dict):
            panel.update(delta)
            if on_update is not None:
                on_update(delta)

        # ... (Etapas 1-5 permanecem as mesmas) ...
        img_bgr = _read_image_bgr(source_image)
        original = img_bgr.copy()
        _emit({"original": original})
        preproc = Preprocessamento.executar(img_bgr)
        _emit({"preproc": preproc})
        edges = Bordas.executar(preproc)
        contours = Contornos.executar(edges)
        contours_overlay = _overlay_contours(original, contours)
        _emit({"contours_overlay": contours_overlay})
        candidatos = FiltrarContornos.executar(contours, img_bgr)
        if not candidatos:
            return { "status": "erro", "texto_final": None, "panel": panel, "etapas": { "original": original, "preprocessamento": preproc, "bordas": edges, "contornos": contours, "candidatos": [] } }
        best = candidatos[0]
        plate_bbox_overlay = _overlay_quad(original, best.get("quad"))
        _emit({"plate_bbox_overlay": plate_bbox_overlay})
        from src.services.analiseCor import AnaliseCor
        crop_bgr = Recorte.executar(img_bgr, best.get("quad"))
        # Convertemos imediatamente para RGB para padronizar
        crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        # Passamos a imagem RGB para as próximas etapas
        percent_azul = AnaliseCor.executar(crop_rgb)
        _emit({"plate_crop": crop_rgb})

        # 6) Binarização (agora retorna uma imagem simples)
        bin_img = Binarizacao.executar(crop_rgb)
        _emit({"binarizacao": bin_img}) # Emitimos a imagem diretamente

        # ... (O resto do pipeline continua o mesmo) ...
        chars = Segmentacao.executar(bin_img)
        _emit({"chars": chars})
        texto_chars = OCR.executarCaracteres(chars)
        texto_raw = OCR.executarImg(bin_img)
        ocr_text_display = f"Segmentado: '{texto_chars}' | Imagem Inteira: '{texto_raw}'"
        _emit({"ocr_text": ocr_text_display})
        texto_final = None
        montagem_final = ""
        if texto_chars:
            montagem_chars = Montagem.executar(texto_chars)
            texto_final = Validacao.executar(montagem_chars)
            montagem_final = montagem_chars
        if not texto_final and texto_raw:
            montagem_raw = Montagem.executar(texto_raw)
            texto_final = Validacao.executar(montagem_raw)
            montagem_final = montagem_raw
        _emit({"plate_text": montagem_final})
        padrao_placa = "INDEFINIDO"
        if texto_final:
            if percent_azul > 0.05: padrao_placa = "MERCOSUL"
            elif len(texto_final) > 4 and texto_final[4].isalpha(): padrao_placa = "MERCOSUL"
            else: padrao_placa = "ANTIGA"
        validation = { "válida": bool(texto_final), "entrada": montagem_final, "saída": texto_final or "", "padrão": padrao_placa }
        _emit({"validation": validation})
        status = "ok" if texto_final else "invalido"
        if texto_final:
            img_annot = plate_bbox_overlay if plate_bbox_overlay is not None else original
            Persistencia.salvar(texto_final, 1.0, original, crop_rgb, img_annot, data_capturada)

        # ATENÇÃO: a chave "binarizacao" aqui agora contém a imagem, não o dicionário
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
                "montagem": montagem_final, 
                "validacao": texto_final 
                } 
            }
    
    @staticmethod
    def consultarRegistros(arg=None, data_inicio: datetime = None, data_fim: datetime = None):
        """
        Consulta registros no banco com filtros opcionais.
        - arg: pode ser dict com {placa, data_inicio, data_fim} ou str com a placa
        - data_fim é inclusiva até 23:59:59 do mesmo dia (sem avançar para o dia seguinte)
        """
        
        placa = None
        if isinstance(arg, dict):
            placa = arg.get("placa")
            data_inicio = arg.get("data_inicio", data_inicio)
            data_fim = arg.get("data_fim", data_fim)
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
                # Agora usamos <= data_fim porque o buscar() já manda 23:59:59 do dia escolhido
                query = query.filter(TabelaAcesso.created_at <= data_fim)

            registros = query.order_by(TabelaAcesso.created_at.desc()).all()
            out = []
            for r in registros:
                img_b64 = None
                if r.plate_crop_image:
                    img_b64 = "data:image/png;base64," + base64.b64encode(r.plate_crop_image).decode("utf-8")

                out.append({
                    "placa": r.plate_text,
                    "data": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "imagem": img_b64,
                })
            return out
        except Exception as e:
            print(f"[ERRO] Erro ao consultar registros: {e}")
            return []
        finally:
            db.close()