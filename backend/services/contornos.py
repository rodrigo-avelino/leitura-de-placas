import cv2
# Classe para detecção de contornos em uma imagem binária para encontrar regiões candidatas a placas de veículos
class Contornos:
    @staticmethod
    def executar(img_edges):
        contornos, _ = cv2.findContours(img_edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return contornos