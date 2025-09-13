import cv2
import numpy as np
import easyocr
import imutils
from datetime import datetime
from config.db import SessionLocal
from models.acessoModel import TabelaAcesso
from pathlib import Path
import uuid
import re

# Diretórios
UPLOAD_DIR = Path("static/uploads")
CROP_DIR = Path("static/crops")
ANNOTATED_DIR = Path("static/annotated")
DEBUG_DIR = Path("static/debug")

for dir_path in [UPLOAD_DIR, CROP_DIR, ANNOTATED_DIR, DEBUG_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

reader = easyocr.Reader(['pt'], gpu=False)

def validar_placa_brasileira(texto):
    if not texto:
        return False, 0.0

    texto_limpo = re.sub(r'[^A-Z0-9]', '', texto.upper())
    padrao_antigo = r'^[A-Z]{3}[0-9]{4}$'
    padrao_mercosul = r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$'

    if re.match(padrao_antigo, texto_limpo):
        return True, 1.0
    elif re.match(padrao_mercosul, texto_limpo):
        return True, 1.0
    return False, 0.0

def preprocessar_imagem_placa(placa_crop):
    if placa_crop is None or placa_crop.size == 0:
        return []

    height, width = placa_crop.shape[:2]
    if width < 100 or height < 30:
        scale_factor = max(100/width, 30/height)
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        placa_crop = cv2.resize(placa_crop, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

    tecnicas = []
    _, bin1 = cv2.threshold(placa_crop, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    tecnicas.append(bin1)

    _, bin2 = cv2.threshold(placa_crop, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    tecnicas.append(bin2)

    bin3 = cv2.adaptiveThreshold(placa_crop, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 11, 2)
    tecnicas.append(bin3)

    bin4 = cv2.adaptiveThreshold(placa_crop, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY_INV, 11, 2)
    tecnicas.append(bin4)

    return tecnicas

def detectar_placa_por_cor(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower_blue = np.array([100, 50, 50])
    upper_blue = np.array([130, 255, 255])
    lower_gray = np.array([0, 0, 50])
    upper_gray = np.array([180, 50, 200])

    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
    mask_gray = cv2.inRange(hsv, lower_gray, upper_gray)
    mask = cv2.bitwise_or(mask_blue, mask_gray)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    return mask

def processar_imagem(img_path: Path):
    print(f"[INFO] Processando imagem: {img_path}")
    image = cv2.imread(str(img_path))
    if image is None:
        print("[ERRO] Imagem não encontrada.")
        return None

    height, width = image.shape[:2]
    if width > 1200:
        scale = 1200 / width
        image = cv2.resize(image, (int(width * scale), int(height * scale)))

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    color_mask = detectar_placa_por_cor(image)

    edges1 = cv2.Canny(blur, 30, 100)
    edges2 = cv2.Canny(blur, 50, 150)
    edges = cv2.bitwise_or(edges1, edges2)
    edges_combined = cv2.bitwise_and(edges, color_mask)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edges_combined = cv2.morphologyEx(edges_combined, cv2.MORPH_CLOSE, kernel)

    contours1 = imutils.grab_contours(cv2.findContours(edges_combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE))
    contours2 = imutils.grab_contours(cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE))
    contours = sorted(contours1 + contours2, key=cv2.contourArea, reverse=True)[:20]

    melhor_resultado = None
    melhor_confianca = 0.0
    melhor_crop = None
    melhor_contorno = None

    for i, c in enumerate(contours):
        area = cv2.contourArea(c)
        if area < 100:
            continue

        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        x, y, w, h = cv2.boundingRect(c)
        aspect_ratio = w / float(h)

        if (area > 500 and 1.8 <= aspect_ratio <= 8.0 and w > 60 and h > 15):
            margin = 5
            y1, y2 = max(0, y - margin), min(gray.shape[0], y + h + margin)
            x1, x2 = max(0, x - margin), min(gray.shape[1], x + w + margin)

            placa_crop_color = image[y1:y2, x1:x2]
            placa_crop = cv2.cvtColor(placa_crop_color, cv2.COLOR_BGR2GRAY)
            placa_crop = cv2.equalizeHist(placa_crop)
            placa_crop = cv2.medianBlur(placa_crop, 3)

            tecnicas_bin = preprocessar_imagem_placa(placa_crop)

            # OCR na imagem colorida direto
            try:
                ocr_results_color = reader.readtext(placa_crop_color)
                for result in ocr_results_color:
                    texto_detectado, conf_ocr = result[1].strip(), result[2]
                    eh_valida, conf_val = validar_placa_brasileira(texto_detectado)
                    conf_final = (conf_ocr * 0.7) + (conf_val * 0.3)

                    if conf_final > melhor_confianca:
                        melhor_resultado = texto_detectado
                        melhor_confianca = conf_final
                        melhor_crop = placa_crop_color
                        melhor_contorno = c
                    if eh_valida and conf_final > 0.8:
                        break
            except Exception as e:
                print(f"[DEBUG] OCR colorido falhou: {e}")

            # OCR nas binarizadas
            for img_bin in tecnicas_bin:
                try:
                    ocr_results = reader.readtext(img_bin)
                    for result in ocr_results:
                        texto_detectado, conf_ocr = result[1].strip(), result[2]
                        eh_valida, conf_val = validar_placa_brasileira(texto_detectado)
                        conf_final = (conf_ocr * 0.7) + (conf_val * 0.3)

                        if conf_final > melhor_confianca:
                            melhor_resultado = texto_detectado
                            melhor_confianca = conf_final
                            melhor_crop = placa_crop_color
                            melhor_contorno = c
                        if eh_valida and conf_final > 0.8:
                            break
                except Exception as e:
                    print(f"[DEBUG] OCR binarizado falhou: {e}")
                    continue

    if melhor_resultado is None or melhor_confianca < 0.3:
        print(f"[INFO] Nenhuma placa detectada com confiança suficiente. Melhor: {melhor_confianca:.3f}")
        return None

    print(f"[INFO] Placa detectada: '{melhor_resultado}' (confiança: {melhor_confianca:.3f})")

    image_anotada = image.copy()
    if melhor_contorno is not None:
        cv2.drawContours(image_anotada, [melhor_contorno], -1, (0, 255, 0), 3)

    unique_id = str(uuid.uuid4())[:8]
    crop_path = CROP_DIR / f"crop_{unique_id}.png"
    anotada_path = ANNOTATED_DIR / f"anotada_{unique_id}.png"

    cv2.imwrite(str(crop_path), melhor_crop)
    cv2.imwrite(str(anotada_path), image_anotada)

    try:
        db = SessionLocal()
        novo_acesso = TabelaAcesso(
            plate_text=melhor_resultado,
            confidence=melhor_confianca,
            source_path=str(img_path),
            plate_crop_path=str(crop_path),
            annotated_path=str(anotada_path),
            created_at=datetime.utcnow()
        )
        db.add(novo_acesso)
        db.commit()
        db.refresh(novo_acesso)
        db.close()

        print(f"[INFO] Registro salvo com ID: {novo_acesso.id}")
        return novo_acesso

    except Exception as e:
        print(f"[ERRO] Falha ao salvar no banco: {e}")
        return None
