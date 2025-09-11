import cv2
import numpy as np
import imutils

def find_plate_bbox(image_bgr):
    """
    Retorna (x,y,w,h) do melhor candidato de placa via contornos + heurísticas.
    Se não encontrar, retorna None.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)  # suaviza preservando bordas
    edged = cv2.Canny(gray, 30, 200)

    cnts = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:20]

    best = None
    best_score = -1

    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            aspect = w / float(h + 1e-6)
            area = w * h
            # heurísticas simples: placa retangular, area mínima e razão
            if 2.0 <= aspect <= 6.5 and area > 5000:
                score = area / (abs(aspect - 4.0) + 1e-6)  # favorece ~4:1
                if score > best_score:
                    best_score = score
                    best = (x, y, w, h)

    return best

def crop_bbox(image_bgr, bbox):
    x, y, w, h = bbox
    H, W = image_bgr.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    return image_bgr[y0:y1, x0:x1]