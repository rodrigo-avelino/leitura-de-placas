import cv2
import numpy as np
import matplotlib.pyplot as plt
# aqui vamos segmentar os caracteres da placa na imagem binária, aplicando várias etapas de filtragem e reconstrução de máscara para melhorar a detecção dos caracteres na imagem binária da placa
class Segmentacao:
    @staticmethod
    def executar(imagem_bin, debug=False):
        h_img, w_img = imagem_bin.shape
        area_total = h_img * w_img
        
        # Etapa 1 e 2: Filtrar contornos e reconstruir a máscara limpa
        contornos_iniciais, _ = cv2.findContours(imagem_bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        mascara_caracteres = np.zeros_like(imagem_bin)
        
        for cnt in contornos_iniciais:
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = h / float(w) if w > 0 else 0
            area_relativa = (w * h) / float(area_total)
            if 1.0 <= aspect_ratio <= 6.0 and 0.003 < area_relativa < 0.25:
                cv2.drawContours(mascara_caracteres, [cnt], -1, (255), -1)

        imagem_limpa = cv2.bitwise_and(imagem_bin, imagem_bin, mask=mascara_caracteres)

        # Etapa 3: Segmentação final na imagem limpa
        contornos_finais, _ = cv2.findContours(imagem_limpa, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # --- NOVA ETAPA DE ELEIÇÃO ---
        # Se encontrarmos mais de 7 contornos, provavelmente há ruído.
        # Vamos eleger os 7 maiores (mais prováveis de serem caracteres).
        if len(contornos_finais) > 7:
            # Calcula a área de cada contorno e os ordena do maior para o menor
            contornos_finais = sorted(contornos_finais, key=cv2.contourArea, reverse=True)
            # Mantém apenas os 7 maiores
            contornos_finais = contornos_finais[:7]

        caracteres = []
        for cnt in contornos_finais:
            x, y, w, h = cv2.boundingRect(cnt)
            roi = imagem_limpa[y:y+h, x:x+w]
            roi = cv2.resize(roi, (32, 64))
            caracteres.append((x, roi))
        
        # Ordena os caracteres da esquerda para a direita
        caracteres = sorted(caracteres, key=lambda c: c[0])

        if debug:
            plt.imshow(imagem_limpa, cmap='gray')
            plt.title('Máscara Limpa com Buracos Preservados')
            plt.show()

        return [c[1] for c in caracteres]