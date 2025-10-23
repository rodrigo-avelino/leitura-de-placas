# src/controllers/placaController.py (Versão Final com Fallback)

import cv2
import base64
import numpy as np
from typing import Any
from pathlib import Path
from io import BytesIO, BufferedReader
from datetime import datetime

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

# --- (Funções auxiliares _overlay_contours, _overlay_quad, _read_image_bgr permanecem iguais) ---
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

def _read_image_bgr(source: Any) -> np.ndarray:
    """ Lê uma imagem de diversas fontes e a normaliza para o formato BGR. """
    if isinstance(source, np.ndarray):
        img = source
        if img.ndim == 3 and img.shape[2] == 3:
            # Assume RGB e converte para BGR se tiver 3 canais
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            return img_bgr
        # Se não for 3 canais, retorna como está (ex: grayscale)
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
        # Tenta converter PIL Image se disponível
        try:
            from PIL import Image
            if isinstance(source, Image.Image):
                rgb_arr = np.array(source.convert("RGB"))
                return cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)
        except ImportError:
            pass # PIL não disponível, continua
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
        panel = {}
        def _emit(delta: dict):
            panel.update(delta)
            if on_update is not None:
                on_update(delta)

        # Etapa 1: Leitura e Preparação
        img_bgr = _read_image_bgr(source_image)
        original = img_bgr.copy()
        _emit({"original": original})

        # Etapas 2 e 3: Pré-processamento, Detecção de Bordas e Contornos
        preproc = Preprocessamento.executar(img_bgr)
        _emit({"preproc": preproc})
        canny_presets = [(50, 150), (100, 200), (150, 250)]
        todos_os_contornos = []
        mapa_de_bordas_visual = np.zeros_like(preproc)
        for (t1, t2) in canny_presets:
            edges = Bordas.executar(preproc, threshold1=t1, threshold2=t2)
            mapa_de_bordas_visual = cv2.bitwise_or(mapa_de_bordas_visual, edges)
            contours = Contornos.executar(edges)
            todos_os_contornos.extend(contours)
        _emit({"contours_overlay": _overlay_contours(original, todos_os_contornos), "bordas": mapa_de_bordas_visual})

        # Etapa 4: Filtrar e Ranqueia Candidatos
        candidatos = FiltrarContornos.executar(todos_os_contornos, img_bgr)
        if not candidatos:
            return { "status": "erro", "texto_final": None, "panel": panel }

        # Guarda o overlay do melhor candidato inicial para o painel
        best_initial = candidatos[0]
        plate_bbox_overlay = _overlay_quad(original, best_initial.get("quad"))
        _emit({"plate_bbox_overlay": plate_bbox_overlay})

        # --- NOVA LÓGICA DE FALLBACK INTELIGENTE ---
        texto_final = None
        crop_final_bgr = None # Guarda o crop da placa encontrada
        NUM_CANDIDATOS_TENTAR = 5
        blue_threshold = 0.12 # Usando o valor otimizado

        for i, candidate in enumerate(candidatos[:NUM_CANDIDATOS_TENTAR]):
            candidate_quad = candidate.get("quad")
            if candidate_quad is None: continue

            print(f"[DEBUG] Tentando candidato #{i+1}...") # Log para debug

            try:
                # 5. Recorte (para o candidato atual)
                crop_bgr = Recorte.executar(img_bgr, candidate_quad)

                # 6. OCR (com crop colorido)
                texto_ocr, confiancas = OCR.executarImg(crop_bgr)

                # 7. Montagem e Validação
                montagem_final = Montagem.executar(texto_ocr)
                placas_validas = Validacao.executar(montagem_final, confiancas)

                if placas_validas: # Encontrou uma leitura válida!
                    # 8. Desambiguação por Cor (usando o crop atual)
                    analise_cores = AnaliseCor.executar(crop_bgr)
                    texto_placa_escolhida = None
                    padrao_placa_escolhida = "INDEFINIDO"

                    if len(placas_validas) == 1:
                        texto_placa_escolhida, padrao_placa_escolhida = placas_validas[0]
                    else:
                        percent_azul_superior = analise_cores.get("percent_azul_superior", 0)
                        if percent_azul_superior > blue_threshold:
                            for placa, padrao in placas_validas:
                                if padrao == "MERCOSUL": texto_placa_escolhida, padrao_placa_escolhida = placa, padrao; break
                        else:
                            for placa, padrao in placas_validas:
                                if padrao == "ANTIGA": texto_placa_escolhida, padrao_placa_escolhida = placa, padrao; break
                        if not texto_placa_escolhida: # Fallback
                             texto_placa_escolhida, padrao_placa_escolhida = placas_validas[0]

                    # Se encontrou um texto final válido, guarda e para o loop
                    if texto_placa_escolhida:
                        texto_final = texto_placa_escolhida
                        padrao_placa = padrao_placa_escolhida
                        crop_final_bgr = crop_bgr # Guarda o crop que deu certo
                        print(f"[INFO] Placa encontrada no candidato #{i+1}: {texto_final}")

                        # Atualiza o painel PDI com os dados do candidato vencedor
                        _emit({"plate_crop": cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)})
                        _emit({"ocr_text": texto_ocr})
                        bin_img_pdi = Binarizacao.executar(crop_bgr)
                        chars_pdi = Segmentacao.executar(bin_img_pdi)
                        _emit({"binarizacao_vencedor": bin_img_pdi, "chars": chars_pdi}) # Usando chave antiga para compatibilidade
                        _emit({"validation": { "válida": True, "saída": texto_final, "padrão": padrao_placa }})

                        break # Sai do loop for i, candidate...

            except Exception as loop_error:
                print(f"[WARN] Erro ao processar candidato #{i+1}: {loop_error}")
                continue # Tenta o próximo candidato

        # --- FIM DA LÓGICA DE FALLBACK ---

        # Se o loop terminou e texto_final AINDA é None, significa que nenhum candidato funcionou
        if texto_final is None:
            print("[INFO] Nenhum candidato produziu uma placa válida após fallback.")
            # Atualiza o painel com o status de falha (pode usar dados do 1o candidato se quiser)
            _emit({"validation": { "válida": False, "saída": "", "padrão": "INDEFINIDO" }})
            return { "status": "invalido", "texto_final": None, "panel": panel }

        # --- PERSISTÊNCIA (Somente se encontrou uma placa válida) ---
        if texto_final and crop_final_bgr is not None:
            img_annot = _overlay_quad(original, best_initial.get("quad")) # Anota o 1o candidato detectado
            if img_annot is None: img_annot = original # Fallback se overlay falhar
            
            # Converte o crop que deu certo para RGB antes de salvar
            crop_rgb_para_salvar = cv2.cvtColor(crop_final_bgr, cv2.COLOR_BGR2RGB)
            Persistencia.salvar(texto_final, 1.0, original, crop_rgb_para_salvar, img_annot, data_capturada)

        return { "status": "ok", "texto_final": texto_final, "panel": panel }


    # --- (Método consultarRegistros permanece o mesmo) ---
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
                    "id": r.id,
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

    @staticmethod
    def excluirRegistro(registro_id: Any) -> bool:
        db = SessionLocal()
        try:
            if registro_id is None:
                return False
                
            # Busca o registro pelo ID (que agora virá do r.id do banco)
            registro = db.query(TabelaAcesso).filter(TabelaAcesso.id == registro_id).first()

            if registro:
                db.delete(registro)
                db.commit()
                # ... (prints e return True)
                return True
            # ... (else e return False)
            return False
        except Exception as e:
            db.rollback()
            # ... (prints de erro e return False)
            return False
        finally:
            db.close()