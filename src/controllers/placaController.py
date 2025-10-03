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

        # Etapa 1: Leitura da Imagem
        img_bgr = _read_image_bgr(source_image)
        original = img_bgr.copy()
        _emit({"original": original})

        # Etapa 2: Pré-processamento
        preproc = Preprocessamento.executar(img_bgr)
        _emit({"preproc": preproc})

        # Etapa 3 e 4: Bordas e Contornos
        edges = Bordas.executar(preproc)
        contours = Contornos.executar(edges)
        _emit({"contours_overlay": _overlay_contours(original, contours)})

        # Etapa 5: Filtrar Contornos para encontrar a placa
        candidatos = FiltrarContornos.executar(contours, img_bgr)
        if not candidatos:
            # Retorna erro se nenhuma placa for encontrada
            return { "status": "erro", "texto_final": None, "panel": panel, "etapas": { "original": original, "preprocessamento": preproc, "bordas": edges, "contornos": contours, "candidatos": [] } }
        
        best = candidatos[0]
        plate_bbox_overlay = _overlay_quad(original, best.get("quad"))
        _emit({"plate_bbox_overlay": plate_bbox_overlay})

        # Etapa 6: Recorte e Análise de Cor
        from src.services.analiseCor import AnaliseCor
        crop_bgr = Recorte.executar(img_bgr, best.get("quad"))
        crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        analise_cores = AnaliseCor.executar(crop_bgr)
        _emit({"plate_crop": crop_rgb})

        # Etapa 7: Binarização
        bin_img = Binarizacao.executar(crop_bgr)
        _emit({"binarizacao": bin_img})

        # Etapa 8: Segmentação (para exibição)
        chars = Segmentacao.executar(bin_img)
        _emit({"chars": chars})

        # Etapa 9: OCR
        texto_ocr, confiancas = OCR.executarImg(bin_img)
        _emit({"ocr_text": texto_ocr})

        # Etapa 10: Montagem
        montagem_final = Montagem.executar(texto_ocr)
        _emit({"plate_text": montagem_final})

        # --- NOVA LÓGICA DE DECISÃO INTELIGENTE ---
        
        # Etapa 11: Validação gera uma lista de possibilidades
        placas_validas = Validacao.executar(montagem_final, confiancas)
        
        texto_final = None
        padrao_placa = "INDEFINIDO"

        if not placas_validas:
            print("[INFO] Nenhuma interpretação de placa válida foi encontrada.")
        elif len(placas_validas) == 1:
            # Se só há uma possibilidade, ela é a correta.
            texto_final, padrao_placa = placas_validas[0]
            print(f"[INFO] Validação única encontrada: {texto_final} ({padrao_placa})")
        else:
            # Se há ambiguidade (ex: pode ser Antiga E Mercosul), usamos a cor para desempatar.
            print(f"[INFO] Ambiguidade detectada: {placas_validas}. Usando cor para decidir.")
            percent_azul = analise_cores["percent_azul"]
            
            if percent_azul > 0.05:
                # Se tem azul, procuramos a opção Mercosul na lista
                for placa, padrao in placas_validas:
                    if padrao == "MERCOSUL":
                        texto_final, padrao_placa = placa, padrao
                        break
            else:
                # Se não tem azul, procuramos a opção Antiga na lista
                for placa, padrao in placas_validas:
                    if padrao == "ANTIGA":
                        texto_final, padrao_placa = placa, padrao
                        break
            
            # Se mesmo assim não achou (caso raro), pega a primeira da lista como fallback
            if not texto_final:
                texto_final, padrao_placa = placas_validas[0]

            print(f"[INFO] Desempate por cor escolheu: {texto_final} ({padrao_placa})")

        # Etapa 12: Preparar resultado para a UI e Persistência
        validation = { "válida": bool(texto_final), "entrada": montagem_final, "saída": texto_final or "", "padrão": padrao_placa }
        _emit({"validation": validation})
        status = "ok" if texto_final else "invalido"
        
        if texto_final:
            img_annot = plate_bbox_overlay if plate_bbox_overlay is not None else original
            Persistencia.salvar(texto_final, 1.0, original, crop_rgb, img_annot, data_capturada)
            
        return { "status": status, "texto_final": texto_final, "panel": panel, "etapas": { "original": original, "preprocessamento": preproc, "bordas": edges, "contornos": contours, "candidatos": candidatos, "recorte": crop_rgb, "binarizacao": bin_img, "segmentacao": chars, "ocr_raw": texto_ocr, "ocr_chars": "", "montagem": montagem_final, "validacao": texto_final } }    
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
