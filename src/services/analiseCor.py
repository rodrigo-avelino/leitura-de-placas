# src/services/analiseCor.py
import cv2
import numpy as np

class AnaliseCor:
    @staticmethod
    def executar(crop_bgr):
        """
        Verifica a porcentagem de azul em uma imagem de placa.
        Retorna um float entre 0.0 e 1.0.
        """
        try:
            h, w = crop_bgr.shape[:2]
            if h == 0 or w == 0: return 0.0

            # Converte para o espaço de cores HSV
            hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_RGB2HSV)

            # Define a faixa de cor para o azul da placa Mercosul
            lower_blue = np.array([95, 80, 50])
            upper_blue = np.array([130, 255, 255])

            # Cria uma máscara que isola apenas os pixels azuis
            mask = cv2.inRange(hsv, lower_blue, upper_blue)

            # Calcula a porcentagem de pixels azuis na imagem
            total_pixels = h * w
            blue_pixels = cv2.countNonZero(mask)

            return blue_pixels / total_pixels
        except Exception:
            return 0.0