import cv2
import matplotlib.pyplot as plt

class Segmentacao:
    @staticmethod
    def executar(imagem_bin, min_area=100, debug=False):
        contornos, _ = cv2.findContours(imagem_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        caracteres = []

        for cnt in contornos:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            aspect = w / float(h)

            # filtro: tamanho mínimo e aspecto razoável
            if area >= min_area and 0.2 <= aspect <= 1.0:
                roi = imagem_bin[y:y+h, x:x+w]
                roi = cv2.resize(roi, (32, 64))  # normaliza
                caracteres.append((x, roi))

        caracteres = sorted(caracteres, key=lambda c: c[0])

        if debug:
            for i, (_, cimg) in enumerate(caracteres):
                plt.subplot(1, len(caracteres), i+1)
                plt.imshow(cimg, cmap='gray')
                plt.axis('off')
            plt.show()

        return [c[1] for c in caracteres]
