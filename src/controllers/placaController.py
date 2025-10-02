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

# ----------------------------------------------------------------------
# Estrutura de diretórios para artefatos visuais (opcional neste MVP).
# Mantemos as pastas criadas por segurança caso, no futuro, a Persistencia
# passe a gravar imagens em disco ao invés de binário no banco.
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
ANNOTATED_DIR = BASE_DIR / "static" / "annotated"
CROP_DIR = BASE_DIR / "static" / "crops"
for d in [ANNOTATED_DIR, CROP_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def _overlay_contours(bgr, contours, color=(0, 255, 255), thickness=2):
    """
    Desenha TODOS os contornos encontrados (para depuração e UI).
    - Entrada:
        bgr       : imagem base (np.ndarray, canal BGR).
        contours  : lista de contornos no formato do OpenCV.
        color     : cor do traço (BGR).
        thickness : espessura do traço.
    - Saída:
        cópia da imagem com contornos sobrepostos, ou None se não houver contornos.
    - Observação:
        Apenas VISUAL. Não altera a lógica de seleção de candidatos.
    """
    if contours is None:
        return None
    out = bgr.copy()
    try:
        cv2.drawContours(out, contours, -1, color, thickness)
    except Exception:
        # Se algum contorno estiver malformado, ignoramos o desenho
        pass
    return out


def _overlay_quad(bgr, quad, color=(0, 255, 0), thickness=2):
    """
    Desenha o quadrilátero do melhor candidato (para depuração e UI).
    - quad deve ser um array (4,2) de pontos (float ou int).
    - Apenas VISUAL; não altera o recorte nem a validação.
    """
    if quad is None:
        return None
    out = bgr.copy()
    q = np.asarray(quad).astype(int)
    pts = q.reshape((-1, 1, 2))
    cv2.polylines(out, [pts], isClosed=True, color=color, thickness=thickness)
    return out


def _read_image_bgr(source: Any) -> np.ndarray:
    """
    Lê imagem de diversas fontes e NORMALIZA para BGR (padrão do OpenCV).
    Aceita:
      - np.ndarray (já carregado; se estiver em RGB, converte para BGR)
      - UploadedFile do Streamlit (possui getbuffer)
      - Objetos de arquivo (BytesIO/BufferedReader)
      - bytes/bytearray/memoryview
      - PIL.Image.Image
      - Caminho (str ou Path)
    Estratégia:
      Sempre que possível usamos np.frombuffer/np.fromfile + cv2.imdecode,
      o que lida melhor com caminhos longos/acentuação/OneDrive no Windows.
    Levanta:
      - FileNotFoundError se o caminho não existir
      - ValueError se imdecode falhar
      - TypeError se o tipo de fonte não for suportado
    """
    # Caso já seja um array numpy
    if isinstance(source, np.ndarray):
        img = source
        # Se tiver 3 canais, assumimos RGB e padronizamos em BGR.
        if img.ndim == 3 and img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return img

    # Arquivo enviado via Streamlit: possui getbuffer()
    if hasattr(source, "getbuffer"):
        data = source.getbuffer()
        n = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(n, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Falha ao decodificar a imagem enviada.")
        return img

    # Objetos de arquivo
    if isinstance(source, (BytesIO, BufferedReader)):
        raw = source.read()
        n = np.frombuffer(raw, dtype=np.uint8)
        img = cv2.imdecode(n, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Falha ao decodificar a imagem (BytesIO).")
        return img

    # Bytes puros
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
        # PIL não disponível ou não é Image; seguimos adiante
        pass

    # Caminho (string/Path)
    if isinstance(source, (str, Path)):
        p = Path(source)
        if not p.exists():
            raise FileNotFoundError(f"Imagem {p} não encontrada")
        # np.fromfile -> lida melhor com caminhos problemáticos no Windows
        data = np.fromfile(str(p), dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Falha ao ler a imagem em {p}")
        return img

    # Tipo não reconhecido
    raise TypeError("Tipo de fonte de imagem não suportado para _read_image_bgr().")


class PlacaController:

    # Em src/controllers/placaController.py
    @staticmethod
    def processarImagem(source_image: Any, data_capturada: datetime, on_update=None):
        panel = {}
        def _emit(delta: dict):
            panel.update(delta)
            if on_update is not None:
                on_update(delta)

        # Etapas 1-7 (Leitura até a Segmentação)
        # ... (esta parte inicial permanece a mesma)
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
        crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        percent_azul = AnaliseCor.executar(crop_rgb)["percent_azul"]
        _emit({"plate_crop": crop_rgb})
        bin_img = Binarizacao.executar(crop_bgr)
        _emit({"binarizacao": bin_img})
        chars = Segmentacao.executar(bin_img)
        _emit({"chars": chars})

        # --- NOVA LÓGICA DE FUSÃO INTELIGENTE DE OCR ---

        # 8) OCR - Executa as duas estratégias
        texto_chars, confiancas_chars = OCR.executarCaracteres(chars)
        texto_raw, _ = OCR.executarImg(bin_img)
        
        ocr_text_display = f"Segmentado: '{texto_chars}' | Imagem Inteira: '{texto_raw}'"
        _emit({"ocr_text": ocr_text_display})

        # 9) Montagem e Criação da Lista de Candidatos Prioritários
        montagem_chars = Montagem.executar(texto_chars)
        montagem_raw = Montagem.executar(texto_raw)
        
        candidatos_ocr = []
        
        # Heurística de limpeza: se o segmentado tem 7 caracteres e está contido no raw (que tem ruído),
        # o segmentado é o candidato de maior prioridade.
        if len(montagem_chars) == 7 and len(montagem_raw) > 7 and montagem_chars in montagem_raw:
            candidatos_ocr.append(montagem_chars)
            candidatos_ocr.append(montagem_raw)
        else:
            # Caso contrário, segue a ordem de prioridade que estabelecemos (raw primeiro)
            candidatos_ocr.append(montagem_raw)
            candidatos_ocr.append(montagem_chars)
        
        # Remove duplicatas e strings vazias
        candidatos_ocr = [c for c in list(dict.fromkeys(candidatos_ocr)) if c]

        print(f"[DEBUG OCR] Candidatos a validar (em ordem de prioridade): {candidatos_ocr}")

        # 10) Validação em Cascata
        texto_final = None
        montagem_final = ""

        for i, cand in enumerate(candidatos_ocr):
            print(f"[DEBUG Validação] Tentativa {i+1} com '{cand}'...")
            # Para a validação do texto segmentado, usamos as confianças.
            # Para os outros, a lista de confianças é vazia.
            confiancas = confiancas_chars if cand == montagem_chars else []
            validado = Validacao.executar(cand, confiancas)
            
            if validado:
                texto_final = validado
                montagem_final = cand # Salva o candidato que deu origem à validação
                print(f"[DEBUG Validação] SUCESSO! Placa final: {texto_final}")
                break # Para na primeira placa válida que encontrar
        
        _emit({"plate_text": montagem_final})

        # O resto do código (a partir da definição do 'padrao_placa') permanece o mesmo...
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

        return { "status": status, "texto_final": texto_final, "panel": panel, "etapas": { "original": original, "preprocessamento": preproc, "bordas": edges, "contornos": contours, "candidatos": candidatos, "recorte": crop_rgb, "binarizacao": bin_img, "segmentacao": chars, "ocr_raw": texto_raw, "ocr_chars": texto_chars, "montagem": montagem_final, "validacao": texto_final } }   
    
    @staticmethod
    def consultarRegistros(arg=None, data_inicio: datetime = None, data_fim: datetime = None):
        """
        Consulta registros de placas no banco com filtros opcionais.

        Parâmetros:
          - arg:
              * dict com chaves opcionais {"placa", "data_inicio", "data_fim"}
                (útil para passar todos os filtros num único objeto)
              * str contendo trecho/placa (filtro simples)
              * None (sem filtro de placa)
          - data_inicio:
              * datetime a partir do qual buscar (>=)
          - data_fim:
              * datetime até o qual buscar (<=)
              * IMPORTANTE: espera-se que a camada de UI já normalize este valor
                para o fim do dia (23:59:59) quando o filtro é por data única.

        Retorno:
          Lista de dicts, cada um com:
            - "placa"  : texto da placa
            - "data"   : string no formato "%Y-%m-%d %H:%M:%S"
            - "imagem" : data URL (base64) do crop da placa, se existir (pronto p/ <img src=...>)
        """
        # Extrai filtros caso um dict tenha sido passado em 'arg'
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

            # Filtro por placa (ilike = case-insensitive, busca parcial)
            if placa:
                query = query.filter(TabelaAcesso.plate_text.ilike(f"%{placa}%"))

            # Janela temporal: início e fim
            if data_inicio:
                query = query.filter(TabelaAcesso.created_at >= data_inicio)
            if data_fim:
                # Inclusivo: usamos <= porque a UI já manda 23:59:59 do dia escolhido.
                query = query.filter(TabelaAcesso.created_at <= data_fim)

            # Ordena do mais recente para o mais antigo
            registros = query.order_by(TabelaAcesso.created_at.desc()).all()

            out = []
            for r in registros:
                # Converte imagem binária (crop) em data URL (base64) para exibir direto no front-end
                img_b64 = None
                if r.plate_crop_image:
                    img_b64 = (
                        "data:image/png;base64," +
                        base64.b64encode(r.plate_crop_image).decode("utf-8")
                    )

                out.append({
                    "placa": r.plate_text,
                    "data": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "imagem": img_b64,
                })

            return out

        except Exception as e:
            # Em produção: registrar stack trace, métricas, etc.
            print(f"[ERRO] Erro ao consultar registros: {e}")
            return []
        finally:
            # Evita vazamento de conexões
            db.close()
