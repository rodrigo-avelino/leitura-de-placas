# src/services/filtrarContornos.py (v4.1 - Guarda o Warp Colorido)

import cv2
import numpy as np
from .binarizacao import Binarizacao
from .analiseCor import AnaliseCor

ASPECT_PATTERNS = {
    "BR_carro_antiga": (3.08, 0.20),
    "BR_carro_mercosul": (2.89, 0.20),
    "BR_moto": (1.18, 0.15)
}

class FiltrarContornos:
    
    # --- (Funções faixa, ordenarPontos, aspectRatio, _calcular_score_segmentacao, 
    #      validacaoGeometrica, _encolher_quad permanecem iguais à v4.0) ---
    @staticmethod
    def faixa(ratio: float):
        best_name, best_score = None, 0.0
        for name, (ideal, tol) in ASPECT_PATTERNS.items():
            diff = abs(ratio - ideal) / ideal
            if diff <= tol:
                score = (1.0 - (diff / tol)) * 0.9
                if score > best_score: best_name, best_score = name, score
        return best_name, best_score

    @staticmethod
    def ordenarPontos(pts):
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0], rect[2] = pts[np.argmin(s)], pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1], rect[3] = pts[np.argmin(diff)], pts[np.argmax(diff)]
        return rect

    @staticmethod
    def aspectRatio(quad):
        (tl, tr, br, bl) = quad
        avg_width = (np.linalg.norm(tr - tl) + np.linalg.norm(br - bl)) / 2.0
        avg_height = (np.linalg.norm(bl - tl) + np.linalg.norm(br - tr)) / 2.0
        return avg_width / max(avg_height, 1e-6), avg_width, avg_height
    
    @staticmethod
    def _calcular_score_segmentacao(warp_bgr):
        try:
            img_bin = Binarizacao.executar(warp_bgr)
            score = Binarizacao._avaliar_qualidade(img_bin) 
            contornos, _ = cv2.findContours(img_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            return score, len(contornos), img_bin, contornos
        except Exception:
            return 0.0, 0, np.zeros((60, 200), dtype=np.uint8), []

    @staticmethod
    def validacaoGeometrica(contour, image_shape):
        H, W = image_shape[:2]
        area = cv2.contourArea(contour)
        if not (0.003 * H * W <= area <= 0.25 * H * W): return False
        x, y, w, h = cv2.boundingRect(contour)
        if w < 50 or h < 15: return False
        margin = min(20, min(W, H) * 0.02)
        if (x < margin or y < margin or (x + w) > (W - margin) or (y + h) > (H - margin)): return False
        if not (0.8 <= w / h <= 6.0): return False
        return True

    @staticmethod
    def _encolher_quad(quad, fator_encolhimento=0.03, max_shrink_ratio=0.15):
        if quad is None: return None
        avg_height = (np.linalg.norm(quad[3] - quad[0]) + np.linalg.norm(quad[2] - quad[1])) / 2.0
        limite_movimento_px = avg_height * max_shrink_ratio
        centroide = quad.mean(axis=0)
        quad_encolhido = np.zeros_like(quad)
        for i in range(4):
            vetor = quad[i] - centroide
            ponto_proposto = quad[i] - (vetor * fator_encolhimento)
            dist_mov = np.linalg.norm(ponto_proposto - quad[i])
            if dist_mov > limite_movimento_px:
                vetor_unitario = vetor / np.linalg.norm(vetor)
                quad_encolhido[i] = quad[i] - (vetor_unitario * limite_movimento_px)
            else:
                quad_encolhido[i] = ponto_proposto
        return quad_encolhido.astype(np.float32)

    @staticmethod
    def executar(contornos, imagem_bgr):
        candidatos, gray = [], cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2GRAY)
        
        # --- GERAÇÃO DE CANDIDATOS (Haar e Contornos) ---
        try:
            cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_russian_plate_number.xml")
            if not cascade.empty():
                detections = cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(40, 15))
                for (x, y, w, h) in detections:
                    quad = np.array([[x, y], [x+w, y], [x+w, y+h], [x, y+h]], dtype="float32")
                    candidatos.append({"quad": quad, "method": "haar"})
        except Exception: print("[WARNING] Erro no Haar Cascade.")

        for contour in contornos:
            if not FiltrarContornos.validacaoGeometrica(contour, imagem_bgr.shape): continue
            quad_approx = cv2.boxPoints(cv2.minAreaRect(contour)).reshape(-1, 1, 2)
            quad = FiltrarContornos.ordenarPontos(quad_approx.reshape(4, 2).astype("float32"))
            candidatos.append({"quad": quad, "method": "contour", "contour_ref": contour})

        if not candidatos: return []
        
        # --- PONTUAÇÃO DE CANDIDATOS (com Análise de Cor) ---
        candidatos_pontuados = []
        for cand in candidatos:
            quad, ratio, avg_w, avg_h = cand["quad"], *FiltrarContornos.aspectRatio(cand["quad"])
            pattern, ar_score = FiltrarContornos.faixa(ratio)
            if pattern is None: continue
            
            warp_para_score = None # Inicializa
            try:
                # Gera o warp BGR para as análises
                warp_para_score = cv2.warpPerspective(imagem_bgr, cv2.getPerspectiveTransform(quad, np.array([[0,0],[200,0],[200,60],[0,60]], dtype="float32")), (200, 60))
            except: continue
            
            # --- EXECUTA AS ANÁLISES ---
            seg_score, num_chars, img_bin, char_contours = FiltrarContornos._calcular_score_segmentacao(warp_para_score)
            analise_cores = AnaliseCor.executar(warp_para_score) 
            
            solidity = 1.0 if cand["method"] == "haar" else cv2.contourArea(cand["contour_ref"]) / max(avg_w * avg_h, 1e-6)
            
            final_score = (ar_score * 1.0) + (seg_score * 4.0) + (solidity * 0.5)
            
            cand.update({
                "pattern": pattern, "score": float(final_score), "score_geom": ar_score, 
                "seg_score": seg_score, "num_chars": num_chars, 
                "bin_image": img_bin, "char_contours": char_contours,
                "analise_cores": analise_cores,
                "warp_colorido": warp_para_score # <<< GUARDA O WARP COLORIDO
            })
            candidatos_pontuados.append(cand)
        
        if not candidatos_pontuados: return []
        
        # --- ORDENAÇÃO E FINALIZAÇÃO ---
        candidatos_pontuados.sort(key=lambda c: c["score"], reverse=True)
        melhor_candidato = candidatos_pontuados[0]
        melhor_candidato["quad"] = FiltrarContornos._encolher_quad(melhor_candidato["quad"], fator_encolhimento=0.02)
        return candidatos_pontuados