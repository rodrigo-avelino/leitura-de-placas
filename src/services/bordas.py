import cv2
import numpy as np

class Bordas:
    @staticmethod
    def executar(imagem_gray):
        bordas = cv2.Canny(imagem_gray, 100, 200)
        return bordas