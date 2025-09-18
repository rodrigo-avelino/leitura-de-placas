import cv2

class Preprocessamento:
    @staticmethod
    def executar(imagem_bgr):
        gray = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2GRAY)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)

        gray_blur = cv2.GaussianBlur(gray, (5, 5), 0)
        return gray_blur
