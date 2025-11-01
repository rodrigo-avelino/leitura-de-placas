import cv2
import numpy as np

class Preprocessamento:
    @staticmethod
    def executar(imagem_bgr):
        # cinza
        gray = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2GRAY)

        # equalização adaptativa (contraste local)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        # redução de ruído preservando bordas
        gray = cv2.bilateralFilter(gray, d=7, sigmaColor=50, sigmaSpace=50)

        # leve sharpening (unsharp mask)
        blur = cv2.GaussianBlur(gray, (0, 0), 1.0)
        sharp = cv2.addWeighted(gray, 1.5, blur, -0.5, 0)

        return sharp
