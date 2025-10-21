# src/services/analiseCor.py

import cv2
import numpy as np

class AnaliseCor:
    @staticmethod
    def executar(crop_bgr):
        """
        Analisa a imagem de uma placa e retorna a porcentagem de pixels
        azuis e vermelhos na imagem inteira E na metade superior.
        Retorna: dict ex: {"percent_azul": 0.1, "percent_vermelho": 0.6, "percent_azul_superior": 0.3}
        """
        try:
            h, w = crop_bgr.shape[:2]
            if h == 0 or w == 0:
                return {"percent_azul": 0.0, "percent_vermelho": 0.0, "percent_azul_superior": 0.0}

            # --- ANÁLISE DA IMAGEM INTEIRA (como antes) ---
            hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
            
            # Faixas de azul e vermelho
            lower_blue = np.array([88, 70, 60]) # H começa em 88
            upper_blue = np.array([135, 255, 255]) # H vai até 135
            mask_blue_total = cv2.inRange(hsv, lower_blue, upper_blue)

            lower_red1 = np.array([0, 70, 50])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 70, 50])
            upper_red2 = np.array([180, 255, 255])
            mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
            mask_red_total = cv2.bitwise_or(mask_red1, mask_red2)

            total_pixels = h * w
            blue_pixels_total = cv2.countNonZero(mask_blue_total)
            red_pixels_total = cv2.countNonZero(mask_red_total)
            
            # --- NOVA ANÁLISE: APENAS METADE SUPERIOR ---
            altura_superior = h // 2 # Pega a metade inteira superior
            if altura_superior > 0:
                # Cria uma máscara que seleciona apenas a metade superior
                mask_roi_superior = np.zeros(crop_bgr.shape[:2], dtype=np.uint8)
                mask_roi_superior[0:altura_superior, :] = 255
                
                # Aplica a máscara de ROI na máscara de cor azul
                mask_blue_superior = cv2.bitwise_and(mask_blue_total, mask_blue_total, mask=mask_roi_superior)
                
                # Calcula a porcentagem de azul NA METADE SUPERIOR
                pixels_regiao_superior = altura_superior * w
                blue_pixels_superior = cv2.countNonZero(mask_blue_superior)
                percent_azul_superior = blue_pixels_superior / pixels_regiao_superior if pixels_regiao_superior > 0 else 0.0
            else:
                percent_azul_superior = 0.0

            return {
                "percent_azul": blue_pixels_total / total_pixels,
                "percent_vermelho": red_pixels_total / total_pixels,
                "percent_azul_superior": percent_azul_superior # Retorna a nova métrica
            }
        except Exception:
            # Retorna valores padrão em caso de erro
            return {"percent_azul": 0.0, "percent_vermelho": 0.0, "percent_azul_superior": 0.0}