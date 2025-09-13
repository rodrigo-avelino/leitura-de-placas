import cv2

class Contornos:
    @staticmethod
    def executar(img_edges):
        contornos, _ = cv2.findContours(img_edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return contornos