# src/services/bordas.py
import cv2
import numpy as np

# Classe para detecção de bordas usando o algoritmo Canny
class Bordas:
    @staticmethod
    def executar(imagem_gray, threshold1=100, threshold2=200):
        """
        Executa a detecção de bordas Canny.
        
        Parâmetros:
          - imagem_gray: Imagem em tons de cinza.
          - threshold1: Primeiro limiar para o procedimento de histerese.
          - threshold2: Segundo limiar para o procedimento de histerese.
        """
        bordas = cv2.Canny(imagem_gray, threshold1, threshold2)
        return bordas