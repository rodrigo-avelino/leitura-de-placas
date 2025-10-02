import cv2
import easyocr
import numpy as np

class OCR:
    reader = easyocr.Reader(['pt', 'en'], gpu=False)
    ALLOWLIST = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

    @staticmethod
    def executarImg(imagem):
        # Para a imagem inteira, pegamos apenas o texto por enquanto.
        # A estratégia principal será a por caracteres.
        resultados = OCR.reader.readtext(
            imagem, 
            detail=0, paragraph=False, allowlist=OCR.ALLOWLIST, text_threshold=0.5
        )
        return (''.join(resultados).strip().upper(), []) # Retorna tupla (texto, lista vazia)

    @staticmethod
    def executarCaracteres(lista_rois_bin):
        """
        Agora retorna uma tupla: (texto_final, lista_de_confianças)
        """
        texto_final = ''
        confiancas = []
        for roi in lista_rois_bin:
            bordered_roi = cv2.copyMakeBorder(roi, 8, 8, 8, 8, cv2.BORDER_CONSTANT, value=[0,0,0])
            roi_rgb = cv2.cvtColor(bordered_roi, cv2.COLOR_GRAY2RGB) if len(bordered_roi.shape) == 2 else bordered_roi
            
            # detail=1 AGORA RETORNA A CONFIAÇA PARA CADA LEITURA
            resultado = OCR.reader.readtext(
                roi_rgb, 
                detail=1, # MUDANÇA IMPORTANTE
                paragraph=False, allowlist=OCR.ALLOWLIST, text_threshold=0.4 # Limiar um pouco mais baixo
            )

            if resultado:
                # resultado é uma lista de tuplas: (bbox, texto, confiança)
                char = resultado[0][1]
                conf = resultado[0][2]
                texto_final += char
                confiancas.append(conf)
            
        return (texto_final.strip().upper(), confiancas)