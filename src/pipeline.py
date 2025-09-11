import cv2
import os
from datetime import datetime
from .config import settings
from .db import SessionLocal, AccessRecord, create_tables
from .detect import find_plate_bbox, crop_bbox
from .ocr import best_plate


def annotate(image_bgr, bbox, text):
    out = image_bgr.copy()
    if bbox is not None:
        x, y, w, h = bbox
        cv2.rectangle(out, (x, y), (x + w, y + h), (0, 255, 0), 2)
    if text:
        cv2.putText(
            out,
            text,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
    return out


def save_image(img_bgr, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cv2.imwrite(path, img_bgr)


def inner_crop(img, ratio=0.08):
    """
    Remove uma borda do recorte para reduzir ruído (ex.: parafusos/aro da moldura).
    ratio=0.08 significa cortar ~8% de cada lado.
    """
    h, w = img.shape[:2]
    dx, dy = int(w * ratio), int(h * ratio)
    x0, y0 = max(0, dx), max(0, dy)
    x1, y1 = max(x0 + 1, w - dx), max(y0 + 1, h - dy)
    return img[y0:y1, x0:x1]


def process_image(path_in: str):
    # Garante que as tabelas existam
    create_tables()

    img = cv2.imread(path_in)
    if img is None:
        raise FileNotFoundError(f"Não foi possível ler a imagem: {path_in}")

    # Detecta a placa (bbox) e recorta
    bbox = find_plate_bbox(img)
    crop = crop_bbox(img, bbox) if bbox is not None else img

    # Recorte interno para o OCR (reduz caracteres falsos nas bordas)
    ocr_input = inner_crop(crop, ratio=0.08)

    # OCR no recorte melhorado; se falhar, tenta na imagem inteira
    plate, conf, cands = best_plate(ocr_input)
    if not plate:
        plate, conf, cands = best_plate(img)

    # Caminhos de saída
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = os.path.splitext(os.path.basename(path_in))[0]
    crop_path = os.path.join(settings.output_dir.as_posix(), f"{stem}_crop_{ts}.jpg")
    out_path = os.path.join(settings.output_dir.as_posix(), f"{stem}_annot_{ts}.jpg")

    # Salva o recorte usado no OCR e a anotação
    save_image(ocr_input, crop_path)  # salva o recorte "limpo" (inner_crop)
    annot = annotate(img, bbox, plate if plate else "(sem leitura)")
    save_image(annot, out_path)

    # Persiste no banco
    session = SessionLocal()
    try:
        rec = AccessRecord(
            plate_text=plate,
            confidence=float(conf),
            source_path=path_in,
            plate_crop_path=crop_path,
            annotated_path=out_path,
        )
        session.add(rec)
        session.commit()
        session.refresh(rec)
        return {
            "id": rec.id,
            "plate_text": plate,
            "confidence": conf,
            "source_path": path_in,
            "crop_path": crop_path,
            "annotated_path": out_path,
            "candidates": cands,
        }
    finally:
        session.close()
