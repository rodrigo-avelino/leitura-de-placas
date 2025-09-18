import cv2
import numpy as np

class Recorte:
    @staticmethod
    def executar(imagem_bgr, quad):
        if quad is None or len(quad) != 4:
            raise ValueError("Quadrilátero inválido para recorte")

        quad = quad.astype("float32")

        Wt, Ht = 400, 130
        dst = np.array([
            [0, 0],
            [Wt - 1, 0],
            [Wt - 1, Ht - 1],
            [0, Ht - 1]
        ], dtype="float32")

        M = cv2.getPerspectiveTransform(quad, dst)
        warp = cv2.warpPerspective(imagem_bgr, M, (Wt, Ht))

        return warp
