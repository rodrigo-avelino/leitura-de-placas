import cv2
import numpy as np

class AnaliseCor:
    @staticmethod
    def executar(crop_bgr):
        """
        Analisa a imagem de uma placa e retorna a porcentagem de pixels
        azuis e vermelhos.
        Retorna: um dicionário ex: {"percent_azul": 0.1, "percent_vermelho": 0.6}
        """
        try:
            h, w = crop_bgr.shape[:2]
            if h == 0 or w == 0: return {"percent_azul": 0.0, "percent_vermelho": 0.0}

            # Converte para o espaço de cores HSV
            hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)

            # --- Detecção de Azul (para Mercosul) ---
            lower_blue = np.array([95, 80, 50])
            upper_blue = np.array([130, 255, 255])
            mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

            # --- Detecção de Vermelho (para táxis, veículos comerciais antigos) ---
            # O vermelho no HSV é dividido em duas faixas (uma perto de 0 e outra perto de 180)
            lower_red1 = np.array([0, 70, 50])
            upper_red1 = np.array([10, 255, 255])
            mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)

            lower_red2 = np.array([170, 70, 50])
            upper_red2 = np.array([180, 255, 255])
            mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
            
            # Combina as duas máscaras de vermelho
            mask_red = cv2.bitwise_or(mask_red1, mask_red2)

            # --- Cálculo das Porcentagens ---
            total_pixels = h * w
            blue_pixels = cv2.countNonZero(mask_blue)
            red_pixels = cv2.countNonZero(mask_red)
            
            return {
                "percent_azul": blue_pixels / total_pixels,
                "percent_vermelho": red_pixels / total_pixels
            }
        except Exception:
            return {"percent_azul": 0.0, "percent_vermelho": 0.0}