# src/services/refinamentoCrop.py
import cv2
import numpy as np

class RefinamentoCrop:
    @staticmethod
    def executar(crop_bgr):
        """
        Aplica duas estratégias de pré-processamento otimizadas (baseadas nos seus testes)
        sobre a imagem da placa recortada.
        Retorna um dicionário com duas imagens em tons de cinza, prontas para a binarização.
        """
        
        # Converte a imagem de entrada para tons de cinza uma única vez
        gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
        
        resultados = {}

        # --- Receita 1: Otimizada para CARACTERES ESCUROS (Black-hat) ---
        # Parâmetros que você encontrou: d=5, sc=22, ss=74, kernel=(11,5)
        suavizada_dark = cv2.bilateralFilter(gray, d=5, sigmaColor=22, sigmaSpace=74)
        kernel_bh = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 5))
        blackhat_result = cv2.morphologyEx(suavizada_dark, cv2.MORPH_BLACKHAT, kernel_bh)
        resultados["para_texto_escuro"] = blackhat_result

        # --- Receita 2: Otimizada para CARACTERES CLAROS (Top-hat) ---
        # Parâmetros que você encontrou: d=5, sc=75, ss=75, kernel=(30,7)
        suavizada_light = cv2.bilateralFilter(gray, d=5, sigmaColor=75, sigmaSpace=75)
        kernel_th = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 7))
        tophat_result = cv2.morphologyEx(suavizada_light, cv2.MORPH_TOPHAT, kernel_th)
        resultados["para_texto_claro"] = tophat_result
        
        return resultados