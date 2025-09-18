import cv2
import easyocr
import numpy as np

class OCR:
    reader = easyocr.Reader(['pt', 'en'], gpu=False)

    @staticmethod
    def executarImg(imagem):
        resultados = OCR.reader.readtext(imagem, detail=0, paragraph=False)
        return ''.join(resultados).strip().upper()

    @staticmethod
    def executarCaracteres(lista_rois_bin):
        texto_final = ''
        for roi in lista_rois_bin:
            roi_rgb = cv2.cvtColor(roi, cv2.COLOR_GRAY2RGB) if len(roi.shape) == 2 else roi
            resultado = OCR.reader.readtext(roi_rgb, detail=0, paragraph=False)
            texto_final += ''.join(resultado)
        return texto_final.strip().upper()
