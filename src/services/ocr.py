import cv2
import easyocr
import numpy as np

class OCR:
    reader = easyocr.Reader(['pt', 'en'], gpu=False)
    
    ALLOWLIST = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

    @staticmethod
    def executarImg(imagem):
        resultados = OCR.reader.readtext(
            imagem, 
            detail=0, 
            paragraph=False,
            allowlist=OCR.ALLOWLIST,
            # Adiciona um limiar de confiança mais baixo
            text_threshold=0.5 
        )
        return ''.join(resultados).strip().upper()

    @staticmethod
    def executarCaracteres(lista_rois_bin):
        texto_final = ''
        for roi in lista_rois_bin:
            bordered_roi = cv2.copyMakeBorder(roi, 8, 8, 8, 8, cv2.BORDER_CONSTANT, value=[0,0,0])
            roi_rgb = cv2.cvtColor(bordered_roi, cv2.COLOR_GRAY2RGB) if len(bordered_roi.shape) == 2 else bordered_roi
            
            resultado = OCR.reader.readtext(
                roi_rgb, 
                detail=0, 
                paragraph=False,
                allowlist=OCR.ALLOWLIST,
                # Adiciona um limiar de confiança mais baixo
                text_threshold=0.5
            )
            texto_final += ''.join(resultado)
            
        return texto_final.strip().upper()