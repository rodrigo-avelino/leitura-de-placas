# src/controllers/placaController.py (v1.3 - Com DELETE)

import cv2
import base64
import numpy as np
from typing import Any
from pathlib import Path
from io import BytesIO, BufferedReader
from datetime import datetime
import sys 

# Importação dos serviços
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

# 💡 Novo import necessário para a exclusão
from sqlalchemy import delete 

# --- Funções Auxiliares de Visualização (Sem alterações) ---

def _overlay_contours(bgr, contours, color=(0, 255, 255), thickness=2):
    """ Desenha todos os contornos encontrados para depuração. """
    if contours is None: return None
    out = bgr.copy()
    try: cv2.drawContours(out, contours, -1, color, thickness)
    except Exception: pass
    return out

def _overlay_quad(bgr, quad, color=(0, 255, 0), thickness=2):
    """ Desenha o quadrilátero do melhor candidato. """
    if quad is None: return None
    out = bgr.copy()
    q = np.asarray(quad).astype(int)
    pts = q.reshape((-1, 1, 2))
    cv2.polylines(out, [pts], isClosed=True, color=color, thickness=thickness)
    return out

def _overlay_filled_quad(image, quad, color=(0, 255, 0), alpha=0.4):
    """ Desenha um quadrilátero preenchido e semi-transparente. """
    overlay = image.copy()
    output = image.copy()
    pts = np.array(quad, dtype=np.int32)
    cv2.fillPoly(overlay, [pts], color)
    cv2.addWeighted(overlay, alpha, output, 1 - alpha, 0, output)
    return output

def _read_image_bgr(source: Any) -> np.ndarray:
    """ Lê uma imagem de diversas fontes e a normaliza para o formato BGR. """
    if isinstance(source, np.ndarray):
        img = source
        if img.ndim == 3 and img.shape[2] == 3:
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            return img_bgr
        return img
    data = None
    if hasattr(source, "getbuffer"): data = source.getbuffer()
    elif isinstance(source, (BytesIO, BufferedReader)): data = source.read()
    elif isinstance(source, (bytes, bytearray, memoryview)): data = source
    elif isinstance(source, (str, Path)):
        p = Path(source)
        if not p.exists(): raise FileNotFoundError(f"Imagem {p} não encontrada")
        data = np.fromfile(str(p), dtype=np.uint8)
    else:
        try:
            from PIL import Image
            if isinstance(source, Image.Image):
                rgb_arr = np.array(source.convert("RGB"))
                return cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)
        except ImportError:
            pass
        raise TypeError(f"Tipo de fonte de imagem não suportado: {type(source)}")
    if data is None: raise ValueError("Não foi possível obter dados da imagem.")
    n = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(n, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Falha ao decodificar a imagem.")
    return img


class PlacaController:

    @staticmethod
    def processarImagem(source_image: Any, data_capturada: datetime, on_update=None):
        # ... (Método processarImagem - Não alterado)
        panel = {}
        def _emit(delta: dict):
            panel.update(delta)
            if on_update is not None:
                on_update(delta)

        # Etapa 1: Leitura e Preparação
        img_bgr = _read_image_bgr(source_image)
        original = img_bgr.copy()
        _emit({"step": "original", "image": original})

        # Etapas 2 e 3: Pré-processamento, Bordas e Contornos
        preproc = Preprocessamento.executar(img_bgr)
        _emit({"step": "preprocessing_done", "image": preproc})
        
        canny_presets = [(50, 150), (100, 200), (150, 250)]
        todos_os_contornos = []
        mapa_de_bordas_visual = np.zeros_like(preproc)
        for (t1, t2) in canny_presets:
            edges = Bordas.executar(preproc, threshold1=t1, threshold2=t2)
            mapa_de_bordas_visual = cv2.bitwise_or(mapa_de_bordas_visual, edges)
            contours = Contornos.executar(edges)
            todos_os_contornos.extend(contours)
        _emit({"step": "contours_done", "image": _overlay_contours(original, todos_os_contornos)})

        # Etapa 4: Filtrar e Ranquear Candidatos
        candidatos = FiltrarContornos.executar(todos_os_contornos, img_bgr)
        if not candidatos:
            _emit({"step": "error", "message": "Nenhum candidato a placa foi encontrado."})
            return { "status": "erro", "texto_final": None, "panel": panel }

        # --- NOVO EVENTO: ENVIAR TOP 5 CANDIDATOS OVERLAY ---
        try:
            overlay_top5 = original.copy()
            cores = [(0, 255, 0), (0, 255, 255), (255, 0, 0), (255, 0, 255), (255, 255, 0)] 
            
            # Desenha do #5 para o #1 (para que #1 fique por cima)
            for i, cand in reversed(list(enumerate(candidatos[:5]))):
                quad = cand.get("quad")
                if quad is not None:
                    cor = cores[i % len(cores)]
                    overlay_top5 = _overlay_filled_quad(overlay_top5, quad, color=cor, alpha=0.4)
                    cv2.polylines(overlay_top5, [np.array(quad, dtype=np.int32)], True, cor, 2)
                    cv2.putText(overlay_top5, f"#{i+1}", (int(quad[0][0]), int(quad[0][1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, cor, 2)
            
            _emit({"step": "top_5_overlay", "image": overlay_top5})
        except Exception as e:
            print(f"[WARN] Erro ao desenhar overlay_top5: {e}", file=sys.stderr)
        # --- FIM DO NOVO EVENTO ---

        # Envia a lista de candidatos (sem imagens, só dados)
        candidatos_para_front = []
        for i, cand in enumerate(candidatos[:5]):
            candidatos_para_front.append({
                "rank": i + 1,
                "score": cand.get('score'),
                "seg_score": cand.get('seg_score'),
                "cores": cand.get('analise_cores'),
            })
        _emit({"step": "candidates_data", "data": candidatos_para_front})


        # --- LÓGICA DE FALLBACK INTELIGENTE ---
        texto_final = None
        padrao_placa = "INDEFINIDO"
        crop_final_bgr = None
        NUM_CANDIDATOS_TENTAR = 5
        blue_threshold = 0.12

        for i, candidate in enumerate(candidatos[:NUM_CANDIDATOS_TENTAR]):
            candidate_quad = candidate.get("quad")
            if candidate_quad is None: continue

            _emit({"step": "fallback_attempt", "candidate_rank": i + 1})

            try:
                crop_bgr = Recorte.executar(img_bgr, candidate_quad)
                # Emite o recorte do candidato que está sendo tentado
                _emit({"step": "candidate_crop_attempt", "candidate_rank": i + 1, "image": crop_bgr})

                texto_ocr, confiancas = OCR.executarImg(crop_bgr)
                montagem_final = Montagem.executar(texto_ocr)
                placas_validas = Validacao.executar(montagem_final, confiancas)

                _emit({
                    "step": "ocr_attempt_result", 
                    "candidate_rank": i + 1, 
                    "ocr_text_raw": texto_ocr,
                    "ocr_text_montado": montagem_final,
                    "valid_plates": placas_validas
                })

                if placas_validas:
                    analise_cores = AnaliseCor.executar(crop_bgr)
                    texto_placa_escolhida = None
                    padrao_placa_escolhida = "INDEFINIDO"

                    if len(placas_validas) == 1:
                        texto_placa_escolhida, padrao_placa_escolhida = placas_validas[0]
                    else:
                        _emit({
                            "step": "color_validation", 
                            "candidate_rank": i + 1, 
                            "data": analise_cores
                        })
                        percent_azul_superior = analise_cores.get("percent_azul_superior", 0)
                        if percent_azul_superior > blue_threshold:
                            for placa, padrao in placas_validas:
                                if padrao == "MERCOSUL": texto_placa_escolhida, padrao_placa_escolhida = placa, padrao; break
                        else:
                            for placa, padrao in placas_validas:
                                if padrao == "ANTIGA": texto_placa_escolhida, padrao_placa_escolhida = placa, padrao; break
                        if not texto_placa_escolhida:
                             texto_placa_escolhida, padrao_placa_escolhida = placas_validas[0]

                    if texto_placa_escolhida:
                        texto_final = texto_placa_escolhida
                        padrao_placa = padrao_placa_escolhida
                        crop_final_bgr = crop_bgr
                        
                        _emit({
                            "step": "candidate_chosen", 
                            "candidate_rank": i + 1, 
                            "placa": texto_final, 
                            "padrao": padrao_placa
                        })

                        # --- NOVOS EVENTOS: BINARIZAÇÃO E SEGMENTAÇÃO DO VENCEDOR ---
                        try:
                            # 1. Binarização
                            bin_img = Binarizacao.executar(crop_bgr)
                            _emit({"step": "final_binarization", "image": bin_img})
                            
                            # 2. Segmentação
                            chars_list = Segmentacao.executar(bin_img)
                            if chars_list:
                                # Tenta concatenar horizontalmente
                                try:
                                    concatenated_chars = np.concatenate(chars_list, axis=1)
                                    _emit({"step": "final_segmentation", "image": concatenated_chars})
                                except ValueError: 
                                    pass 
                        except Exception as e:
                            print(f"[WARN] Erro ao gerar imagens de binarização/segmentação: {e}", file=sys.stderr)
                        # --- FIM DOS NOVOS EVENTOS ---

                        break

            except Exception as loop_error:
                _emit({"step": "error", "message": f"Erro ao processar candidato #{i+1}: {loop_error}"})
                continue

        # --- FIM DA LÓGICA DE FALLBACK ---

        if texto_final is None:
            _emit({"step": "fallback_failed_all", "message": "Nenhum candidato produziu placa válida"})
            return { "status": "invalido", "texto_final": None, "panel": panel }

        # --- PERSISTÊNCIA ---
        if texto_final and crop_final_bgr is not None:
            img_annot = overlay_top5 if 'overlay_top5' in locals() else _overlay_quad(original, candidate_quad)
            if img_annot is None: img_annot = original
            
            crop_rgb_para_salvar = cv2.cvtColor(crop_final_bgr, cv2.COLOR_BGR2RGB)
            Persistencia.salvar(
                texto_final, 1.0, original, 
                crop_rgb_para_salvar, img_annot, data_capturada,
                placa_padrao=padrao_placa
            )

        return { 
            "status": "ok", 
            "texto_final": texto_final, 
            "padrao_placa": padrao_placa,
            "panel": panel 
        }

    # --- MÉTODO DE CONSULTA DE REGISTROS (Sem alterações) ---
    @staticmethod
    def consultarRegistros(arg=None, data_inicio: datetime = None, data_fim: datetime = None):
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
                    "tipo_placa": r.plate_type 
                })
            return out
        except Exception as e:
            print(f"[ERRO] Erro ao consultar registros: {e}")
            return []
        finally:
            db.close()
            
    # --- NOVO MÉTODO: DELETAR REGISTRO ---
    @staticmethod
    def deletarRegistro(id: int) -> bool:
        """
        Deleta um registro no banco de dados com base no ID.
        Retorna True se deletou (1 ou mais linhas afetadas), False caso contrário.
        """
        db = SessionLocal()
        try:
            # Constrói a declaração DELETE
            stmt = delete(TabelaAcesso).where(TabelaAcesso.id == id)
            
            # Executa a declaração
            result = db.execute(stmt)
            
            # Commit para efetivar a exclusão
            db.commit()
            
            # Retorna True se pelo menos uma linha foi afetada
            return result.rowcount > 0
            
        except Exception as e:
            print(f"[ERRO] Erro ao deletar registro {id}: {e}", file=sys.stderr)
            db.rollback()
            return False
        finally:
            db.close()