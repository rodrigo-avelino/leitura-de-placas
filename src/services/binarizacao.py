import cv2
from matplotlib import pyplot as plt

class Binarizacao:
    @staticmethod
    def executar(imagem_bgr, metodo='adaptive_mean', invertido=False, debug=False):
        gray = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2GRAY)

        if metodo == 'adaptive_mean':
            bin_img = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_MEAN_C,
                cv2.THRESH_BINARY_INV if invertido else cv2.THRESH_BINARY,
                blockSize=25,
                C=15
            )
        elif metodo == 'adaptive_gaussian':
            bin_img = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV if invertido else cv2.THRESH_BINARY,
                blockSize=25,
                C=15
            )
        elif metodo == 'otsu':
            _, bin_img = cv2.threshold(
                gray, 0, 255,
                (cv2.THRESH_BINARY_INV if invertido else cv2.THRESH_BINARY) + cv2.THRESH_OTSU
            )
        else:
            raise ValueError(f"Método de binarização desconhecido: {metodo}")

        if debug:
            plt.imshow(bin_img, cmap='gray')
            plt.title(f'Binarização: {metodo} {"(invertida)" if invertido else ""}')
            plt.axis('off')
            plt.show()

        return bin_img
