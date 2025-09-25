import cv2
import easyocr
import numpy as np

class OCR:
    # Instância única do leitor do EasyOCR carregada para PT/EN.
    # gpu=False força execução em CPU (mais compatível em Windows/ambientes sem CUDA).
    reader = easyocr.Reader(['pt', 'en'], gpu=False)
    
    # Conjunto de caracteres permitido. Restringir o alfabeto ajuda a reduzir
    # erros do OCR (placas só usam A–Z e 0–9).
    ALLOWLIST = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

    @staticmethod
    def executarImg(imagem):
        """
        Realiza OCR na imagem inteira da placa (geralmente o recorte/warp já pré-processado).
        - imagem: array (RGB/BGR/GRAY aceito pelo EasyOCR).
        Retorna: string com os caracteres detectados (uppercase, sem espaços).
        """
        resultados = OCR.reader.readtext(
            imagem, 
            detail=0,          # detail=0 => retorna apenas o texto (sem boxes/confiança)
            paragraph=False,   # não tenta juntar várias linhas como um parágrafo
            allowlist=OCR.ALLOWLIST,  # restringe o alfabeto ao de placas
            text_threshold=0.5 # limiar mais permissivo para o mapa de texto da rede (pega textos mais fracos)
        )
        # Junta possíveis pedaços em uma única string e normaliza
        return ''.join(resultados).strip().upper()

    @staticmethod
    def executarCaracteres(lista_rois_bin):
        """
        Faz OCR por caractere (ou pequenos grupos), usando as ROIs segmentadas (binárias).
        - lista_rois_bin: lista de imagens (normalmente 1 canal, binárias) para cada caractere.
        Estratégia:
          1) Adiciona uma borda preta ao redor da ROI para dar 'respiro' ao OCR.
          2) Converte para RGB se vier em escala de cinza.
          3) Aplica EasyOCR com o mesmo allowlist e threshold.
          4) Concatena os resultados parciais.
        Retorna: string final (uppercase, sem espaços extras).
        """
        texto_final = ''
        for roi in lista_rois_bin:
            # Borda preta ao redor reduz recortes "colados" na borda e melhora acerto do OCR
            bordered_roi = cv2.copyMakeBorder(
                roi, 8, 8, 8, 8,
                cv2.BORDER_CONSTANT,
                value=[0, 0, 0]
            )
            # EasyOCR espera 3 canais; se for GRAY, converte para RGB
            roi_rgb = (
                cv2.cvtColor(bordered_roi, cv2.COLOR_GRAY2RGB)
                if len(bordered_roi.shape) == 2 else bordered_roi
            )
            
            resultado = OCR.reader.readtext(
                roi_rgb, 
                detail=0,
                paragraph=False,
                allowlist=OCR.ALLOWLIST,
                text_threshold=0.5
            )
            # Acrescenta o texto detectado para esta ROI
            texto_final += ''.join(resultado)
            
        # Normaliza e retorna
        return texto_final.strip().upper()
