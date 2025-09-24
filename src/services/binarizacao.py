import cv2
import numpy as np
from matplotlib import pyplot as plt

class Binarizacao:

    @staticmethod
    def _avaliar_qualidade(img_bin):
        """
        Função 'juiz' com critérios finais e MUITO MAIS FLEXÍVEIS.
        """
        contornos, _ = cv2.findContours(img_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        candidatos_validos = []
        h_img, w_img = img_bin.shape
        area_total = h_img * w_img

        for cnt in contornos:
            x, y, w, h = cv2.boundingRect(cnt)
            
            aspect_ratio = h / float(w) if w > 0 else 0
            area_relativa = (w * h) / float(area_total)
            hull = cv2.convexHull(cnt)
            solidity = cv2.contourArea(cnt) / float(cv2.contourArea(hull)) if cv2.contourArea(hull) > 0 else 0

            # --- CRITÉRIOS SIGNIFICATIVAMENTE RELAXADOS ---
            # Aceitamos caracteres menos sólidos e com proporções mais variadas.
            if 1.0 <= aspect_ratio <= 6.0 and 0.003 < area_relativa < 0.30 and solidity > 0.4:
                candidatos_validos.append({"x": x, "y": y, "w": w, "h": h})
        
        num_candidatos = len(candidatos_validos)
        
        # Aceitamos um número menor de caracteres encontrados
        if num_candidatos < 3 or num_candidatos > 9:
            return 0.0

        # O resto da lógica de pontuação permanece
        alturas = [c['h'] for c in candidatos_validos]
        std_alturas = np.std(alturas)
        mediana_alturas = np.median(alturas)
        score_altura = max(0, 1.0 - (std_alturas / mediana_alturas)) if mediana_alturas > 0 else 0

        centros_y = [c['y'] + c['h']/2 for c in candidatos_validos]
        std_y = np.std(centros_y)
        score_alinhamento = max(0, 1.0 - (std_y / h_img) * 2.0)

        score_numero = 1.0 - (abs(7 - num_candidatos) / 7.0)
        score_final = (score_numero * 0.4) + (score_altura * 0.3) + (score_alinhamento * 0.3)
        
        return score_final

    @staticmethod
    def executar(imagem_bgr, debug=False):
        # A lógica interna para pré-processamento, geração e avaliação de candidatos permanece a mesma
        gray = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray_enhanced = clahe.apply(gray)
        gray_enhanced = cv2.bilateralFilter(gray_enhanced, d=5, sigmaColor=75, sigmaSpace=75)
        hsv = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2HSV)
        candidatos_dict = {}
        kernel_bh = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 5))
        blackhat = cv2.morphologyEx(gray_enhanced, cv2.MORPH_BLACKHAT, kernel_bh)
        _, cand_blackhat = cv2.threshold(blackhat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        candidatos_dict['blackhat_otsu'] = cand_blackhat
        kernel_th = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 5))
        tophat = cv2.morphologyEx(gray_enhanced, cv2.MORPH_TOPHAT, kernel_th)
        _, cand_tophat = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        candidatos_dict['tophat_otsu'] = cand_tophat
        lower_black = np.array([0, 0, 0])
        upper_black = np.array([180, 255, 100])
        hsv_dark_mask = cv2.inRange(hsv, lower_black, upper_black)
        candidatos_dict['hsv_dark'] = hsv_dark_mask
        lower_white = np.array([0, 0, 160])
        upper_white = np.array([180, 70, 255])
        candidatos_dict['hsv_light'] = cv2.inRange(hsv, lower_white, upper_white)
        adaptive_binary = cv2.adaptiveThreshold(gray_enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10)
        candidatos_dict['adaptive_inv'] = cv2.bitwise_not(adaptive_binary)
        candidatos_dict['hsv_dark_inverso'] = cv2.bitwise_not(hsv_dark_mask)
        _, otsu_binary = cv2.threshold(gray_enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        candidatos_dict['otsu_inv'] = cv2.bitwise_not(otsu_binary)

        candidatos_avaliados = []
        for nome, img_bin in candidatos_dict.items():
            score = Binarizacao._avaliar_qualidade(img_bin)
            candidatos_avaliados.append({"nome": nome, "score": score, "imagem": img_bin})

        candidatos_avaliados.sort(key=lambda x: x["score"], reverse=True)
        melhor_candidato = candidatos_avaliados[0]

        # Se o melhor candidato tiver score baixo, retorna imagem preta.
        if melhor_candidato['score'] < 0.1:
            return np.zeros_like(gray)

        melhor_tecnica = melhor_candidato["imagem"]

        # Limpeza final
        kernel_final = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        resultado_final = cv2.morphologyEx(melhor_tecnica, cv2.MORPH_OPEN, kernel_final, iterations=1)
        resultado_final = cv2.morphologyEx(resultado_final, cv2.MORPH_CLOSE, kernel_final, iterations=1)

        # A função agora retorna APENAS a imagem final
        return resultado_final