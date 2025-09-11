import re
import cv2
import numpy as np
import easyocr

# pt/en/es ajuda em placas LATAM
_reader = easyocr.Reader(['pt', 'en', 'es'], gpu=False)

# Padrões aceitos
PLATE_PATTERNS = [
    re.compile(r'^[A-Z]{3}\d{4}$'),        # BR antigo: AAA9999
    re.compile(r'^[A-Z]{3}\d[A-Z]\d{2}$'), # BR Mercosul: AAA9A99
    re.compile(r'^[A-Z]{2}\d{4}$'),        # 2L-4D: CC5220
    re.compile(r'^[A-Z]{3}\d{3}$'),        # 3L-3D: ABC123
    re.compile(r'^[A-Z]{2}\d{3}[A-Z]{2}$') # AR Mercosul: AA000AA
]

AMBIGUOUS_MAP = {"O":"0","0":"O","I":"1","1":"I","S":"5","5":"S","B":"8","8":"B","Z":"2","2":"Z"}

def normalize_text(s: str) -> str:
    s = s.upper()
    return re.sub(r'[^A-Z0-9]', '', s)

def generate_corrections(s: str):
    vars = {s}
    for a,b in AMBIGUOUS_MAP.items():
        if a in s:
            vars.add(s.replace(a,b))
    return list(vars)

def is_valid_plate(s: str) -> bool:
    return any(p.match(s) for p in PLATE_PATTERNS)

def _preprocess_for_ocr(image_bgr):
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

def _read_ocr(image_bgr):
    img_rgb = image_bgr[:, :, ::-1]
    results = _reader.readtext(img_rgb, detail=1, paragraph=False,
                               allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -")
    return [(text, float(conf)) for (_, text, conf) in results]

def _windows(s: str, min_len=5, max_len=8):
    for L in range(max_len, min_len-1, -1):
        for i in range(0, len(s)-L+1):
            yield s[i:i+L]

def read_plate_candidates(image_bgr):
    img = _preprocess_for_ocr(image_bgr)
    raw = _read_ocr(img)

    best = {}
    for text, conf in raw:
        norm = normalize_text(text)
        if not norm:
            continue
        for win in _windows(norm):
            for variant in generate_corrections(win):
                if is_valid_plate(variant):
                    # pequena penalização se usar janela (caracter extra removido)
                    adj = conf * (len(win) / max(len(norm), 1))
                    if variant not in best or adj > best[variant]:
                        best[variant] = adj
                    break
    return sorted(best.items(), key=lambda x: x[1], reverse=True)

def read_plate_fallback(image_bgr):
    img = _preprocess_for_ocr(image_bgr)
    raw = _read_ocr(img)
    best = {}
    for text, conf in raw:
        norm = normalize_text(text)
        if 4 <= len(norm) <= 8:
            if norm not in best or conf > best[norm]:
                best[norm] = conf
    return sorted(best.items(), key=lambda x: x[1], reverse=True)

def best_plate(image_bgr, allow_fallback=True):
    cands = read_plate_candidates(image_bgr)
    if cands:
        return cands[0][0], cands[0][1], cands
    if allow_fallback:
        raw = read_plate_fallback(image_bgr)
        if raw:
            return raw[0][0], raw[0][1], raw
    return None, 0.0, []
