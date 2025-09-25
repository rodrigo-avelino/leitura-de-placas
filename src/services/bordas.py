import cv2
import numpy as np
# Classe para detecção de bordas usando o algoritmo Canny
class Bordas:
    @staticmethod
    def executar(imagem_gray):
        bordas = cv2.Canny(imagem_gray, 100, 200)
        return bordas