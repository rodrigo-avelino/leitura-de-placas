# src/controllers/placaController.py

import cv2
import base64
import numpy as np
from typing import Any
from pathlib import Path
from io import BytesIO, BufferedReader
from datetime import datetime

# Importação dos serviços que compõem o pipeline
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
from src.services.analiseCor import AnaliseCor

# Importação do modelo e da sessão do banco de dados
from src.models.acessoModel import TabelaAcesso
from src.config.db import SessionLocal


# --- Funções Auxiliares de Visualização ---

def _overlay_contours(bgr, contours, color=(0, 255, 255), thickness=2):
    """ Desenha todos os contornos encontrados para depuração. """
    if contours is None:
        return None
    out = bgr.copy()
    try:
        cv2.drawContours(out, contours, -1, color, thickness)
    except Exception:
        pass
    return out


def _overlay_quad(bgr, quad, color=(0, 255, 0), thickness=2):
    """ Desenha o quadrilátero do melhor candidato. """
    if quad is None:
        return None
    out = bgr.copy()
    q = np.asarray(quad).astype(int)
    pts = q.reshape((-1, 1, 2))
    cv2.polylines(out, [pts], isClosed=True, color=color, thickness=thickness)
    return out


def _read_image_bgr(source: Any) -> np.ndarray:
    """ Lê uma imagem de diversas fontes e a normaliza para o formato BGR. """
    if isinstance(source, np.ndarray):
        img = source
        if img.ndim == 3 and img.shape[2] == 3:
            return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return img

    if hasattr(source, "getbuffer"):
        data = source.getbuffer()
    elif isinstance(source, (BytesIO, BufferedReader)):
        data = source.read()
    elif isinstance(source, (bytes, bytearray, memoryview)):
        data = source
    elif isinstance(source, (str, Path)):
        p = Path(source)
        if not p.exists(): raise FileNotFoundError(f"Imagem {p} não encontrada")
        data = np.fromfile(str(p), dtype=np.uint8)
    else:
        raise TypeError("Tipo de fonte de imagem não suportado.")
    
    n = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(n, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Falha ao decodificar a imagem.")
    return img


class PlacaController:

    @staticmethod
    def processarImagem(source_image: Any, data_capturada: datetime, on_update=None):
        panel = {}
        def _emit(delta: dict):
            panel.update(delta)
            if on_update is not None:
                on_update(delta)

        # Etapa 1: Leitura e Preparação da Imagem
        img_bgr = _read_image_bgr(source_image)
        original = img_bgr.copy()
        _emit({"original": original})

        # Etapa 2: Pré-processamento para Detecção de Bordas
        preproc = Preprocessamento.executar(img_bgr)
        _emit({"preproc": preproc})

        # Etapa 3: Detecção de Bordas e Contornos (Estratégia Multi-Passadas)
        canny_presets = [(50, 150), (100, 200), (150, 250)]
        todos_os_contornos = []
        mapa_de_bordas_visual = np.zeros_like(preproc)
        for (t1, t2) in canny_presets:
            edges = Bordas.executar(preproc, threshold1=t1, threshold2=t2)
            mapa_de_bordas_visual = cv2.bitwise_or(mapa_de_bordas_visual, edges)
            contours = Contornos.executar(edges)
            todos_os_contornos.extend(contours)
        _emit({"contours_overlay": _overlay_contours(original, todos_os_contornos), "bordas": mapa_de_bordas_visual})

        # Etapa 4: Filtrar e Ranqueia Candidatos (Coração da Lógica de Detecção)
        candidatos = FiltrarContornos.executar(todos_os_contornos, img_bgr)
        if not candidatos:
            return { "status": "erro", "texto_final": None, "panel": panel }
        
        best = candidatos[0]
        plate_bbox_overlay = _overlay_quad(original, best.get("quad"))
        _emit({"plate_bbox_overlay": plate_bbox_overlay})

        # Etapa 5: Recorte da Placa (Colorido)
        crop_bgr = Recorte.executar(img_bgr, best.get("quad"))
        _emit({"plate_crop": cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)}) # Envia RGB para o painel
        
        # --- FLUXO DE OCR VENCEDOR ---

        # Etapa 6: OCR (usa o recorte colorido BGR diretamente)
        texto_ocr, confiancas = OCR.executarImg(crop_bgr)
        _emit({"ocr_text": texto_ocr})
        
        # Etapas de PDI (Binarização e Segmentação) apenas para VISUALIZAÇÃO
        bin_img_pdi = Binarizacao.executar(crop_bgr)
        chars_pdi = Segmentacao.executar(bin_img_pdi)
        _emit({"binarizacao": bin_img_pdi, "chars": chars_pdi})

        # --- FLUXO DE VALIDAÇÃO E PERSISTÊNCIA ---

        # Etapa 7: Montagem e Validação do Texto
        montagem_final = Montagem.executar(texto_ocr)
        placas_validas = Validacao.executar(montagem_final, confiancas)
        
        # Etapa 8: Lógica de Negócio (Desempate por Cor)
        analise_cores = AnaliseCor.executar(crop_bgr)
        texto_final, padrao_placa = None, "INDEFINIDO"

        if not placas_validas:
            pass # Sem texto válido
        elif len(placas_validas) == 1:
            texto_final, padrao_placa = placas_validas[0]
        else: 
            percent_azul = analise_cores.get("percent_azul", 0)
            if percent_azul > 0.05:
                for placa, padrao in placas_validas:
                    if padrao == "MERCOSUL": texto_final, padrao_placa = placa, padrao; break
            else:
                for placa, padrao in placas_validas:
                    if padrao == "ANTIGA": texto_final, padrao_placa = placa, padrao; break
            if not texto_final: texto_final, padrao_placa = placas_validas[0] # Fallback

        validation = { "válida": bool(texto_final), "saída": texto_final or "", "padrão": padrao_placa }
        _emit({"validation": validation})
        
        # Etapa 9: Persistência no Banco
        if texto_final:
            img_annot = plate_bbox_overlay if plate_bbox_overlay is not None else original
            # Converte o crop de BGR para RGB antes de salvar
            crop_rgb_para_salvar = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
            Persistencia.salvar(texto_final, 1.0, original, crop_rgb_para_salvar, img_annot, data_capturada)
            
        return { "status": "ok" if texto_final else "invalido", "texto_final": texto_final, "panel": panel }


    @staticmethod
    def consultarRegistros(arg=None, data_inicio: datetime = None, data_fim: datetime = None):
        """ Consulta registros de placas no banco com filtros opcionais. """
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