# src/services/binarizacao.py

import cv2
import numpy as np

class Binarizacao:

    @staticmethod
    def _avaliar_qualidade(img_bin):
        """
        A função 'juiz' inteligente que avalia a qualidade de uma binarização
        com base em múltiplos critérios (quantidade, geometria, alinhamento).
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
            # Critérios para um blob ser considerado um caractere plausível
            if 1.0 <= aspect_ratio <= 7.0 and 0.003 < area_relativa < 0.40 and solidity > 0.4:
                candidatos_validos.append({"x": x, "y": y, "w": w, "h": h})
        
        num_candidatos = len(candidatos_validos)
        if num_candidatos < 3 or num_candidatos > 9:
            return 0.0

        alturas = [c['h'] for c in candidatos_validos]
        score_altura = max(0, 1.0 - (np.std(alturas) / np.median(alturas))) if np.median(alturas) > 0 else 0
        
        centros_y = [c['y'] + c['h']/2 for c in candidatos_validos]
        score_alinhamento = max(0, 1.0 - (np.std(centros_y) / h_img) * 2.0)
        
        score_numero = 1.0 - (abs(7 - num_candidatos) / 7.0)
        
        # Score final ponderado
        score_final = (score_numero * 0.4) + (score_altura * 0.3) + (score_alinhamento * 0.3)
        return score_final

    @staticmethod
    def executar(imagem_bgr):
        """
        Gera dois candidatos de binarização usando as receitas otimizadas (black-hat e top-hat)
        e usa o 'juiz' para escolher e retornar o melhor resultado.
        """
        if imagem_bgr is None or imagem_bgr.size == 0:
            return np.zeros((60, 200), dtype=np.uint8)
            
        gray = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2GRAY)
        candidatos_dict = {}

        # Candidato 1: Receita para texto ESCURO (Black-hat)
        suavizada_dark = cv2.bilateralFilter(gray, d=5, sigmaColor=75, sigmaSpace=75)
        kernel_bh = cv2.getStructuringElement(cv2.MORPH_RECT, (38, 3))
        blackhat = cv2.morphologyEx(suavizada_dark, cv2.MORPH_BLACKHAT, kernel_bh)
        _, cand_dark = cv2.threshold(blackhat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        candidatos_dict['refino_dark'] = cand_dark
        
        # Candidato 2: Receita para texto CLARO (Top-hat)
        suavizada_light = cv2.bilateralFilter(gray, d=5, sigmaColor=75, sigmaSpace=75)
        kernel_th = cv2.getStructuringElement(cv2.MORPH_RECT, (45, 5))
        tophat = cv2.morphologyEx(suavizada_light, cv2.MORPH_TOPHAT, kernel_th)
        _, cand_light = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        candidatos_dict['refino_light'] = cand_light

        # O JUIZ DECIDE O VENCEDOR
        melhor_nome, maior_score = None, -0.1
        for nome, img_bin in candidatos_dict.items():
            score = Binarizacao._avaliar_qualidade(img_bin)
            if score > maior_score:
                maior_score, melhor_nome = score, nome
        
        if melhor_nome is None or maior_score < 0.1:
            return np.zeros_like(gray) # Retorna preto se nenhum candidato for bom

        return candidatos_dict[melhor_nome]