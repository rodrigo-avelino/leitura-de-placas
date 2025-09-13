import cv2
import numpy as np

ASPECT_PATTERNS = {
    "BR_carro_antiga": (3.08, 0.20),
    "BR_carro_mercosul": (2.89, 0.20),
    "BR_moto": (1.18, 0.15),
    "US_carro": (2.00, 0.15),
    "EU_carro": (4.73, 0.15),
}

class FiltrarContornos:
    
    @staticmethod
    def faixa(ratio: float):
        #retorna score baseado na proximidade do aspect ratio ideal
        best_name, best_score = None, 0.0
        
        for name, (ideal, tol) in ASPECT_PATTERNS.items():
            #calcula diferença normalizada
            diff = abs(ratio - ideal) / ideal
            
            #so considera se está dentro da tolerância
            if diff <= tol:
                score = (1.0 - (diff / tol)) * 0.9
                if score > best_score:
                    best_name, best_score = name, score
        
        return best_name, best_score

    @staticmethod
    def ordenarPontos(pts):
        rect = np.zeros((4, 2), dtype="float32")
        
        # Soma das coordenadas
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]   #menor soma
        rect[2] = pts[np.argmax(s)]   #maior soma
        
        # Diferença das coordenadas
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]  #menor diferença
        rect[3] = pts[np.argmax(diff)]  #maior diferença
        
        return rect

    @staticmethod
    def aspectRatio(quad):
        # calcula o aspect ratio do quadrilátero
        (tl, tr, br, bl) = quad
        
        #larguras
        width_top = np.linalg.norm(tr - tl)
        width_bottom = np.linalg.norm(br - bl)
        
        #alturas
        height_left = np.linalg.norm(bl - tl)
        height_right = np.linalg.norm(br - tr)
        
        #media
        avg_width = (width_top + width_bottom) / 2.0
        avg_height = (height_left + height_right) / 2.0
        
        return avg_width / max(avg_height, 1e-6), avg_width, avg_height

    @staticmethod
    def calculoTexto(warp_rgb):
        gray = cv2.cvtColor(warp_rgb, cv2.COLOR_RGB2GRAY)
        
        #binarizacao adaptativa para destacar caracteres
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        #possiveis caracteres
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(255 - binary)
        
        #contar componentes que podem ser caracteres
        char_count = 0
        h, w = gray.shape
        min_char_area = (h * w) * 0.01  # Mínimo 1% da área
        max_char_area = (h * w) * 0.25  # Máximo 25% da área
        
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if min_char_area <= area <= max_char_area:
                # Verifica aspect ratio do componente
                comp_w = stats[i, cv2.CC_STAT_WIDTH]
                comp_h = stats[i, cv2.CC_STAT_HEIGHT]
                if comp_h > 0:
                    comp_ratio = comp_w / comp_h
                    # Caracteres típicos têm ratio entre 0.3 e 2.0
                    if 0.3 <= comp_ratio <= 2.0:
                        char_count += 1
        
        return min(1.0, char_count / 7.0)

    @staticmethod
    def validacaoGeometrica(contour, image_shape):
        H, W = image_shape[:2]
        
        #area minima e maxima
        area = cv2.contourArea(contour)
        min_area = 0.003 * H * W  # reduzido para placas distantes
        max_area = 0.25 * H * W   # reduzindo para evitar falsos positivos
        
        if area < min_area or area > max_area:
            return False, "area_invalid"
        
        #validacao basicas
        x, y, w, h = cv2.boundingRect(contour)
        
        #dimensao minima
        if w < 50 or h < 15:
            return False, "too_small"
    
        margin = min(20, min(W, H) * 0.02)
        if (x < margin or y < margin or 
            (x + w) > (W - margin) or (y + h) > (H - margin)):
            return False, "edge_proximity"
        
        basic_ratio = w / h
        if basic_ratio < 0.8 or basic_ratio > 6.0:
            return False, "basic_ratio"
        
        return True, "valid"

    @staticmethod
    def warpProjetado(bgr, quad, target_ratio):
        #tamanhos baseados no tipo de placa
        if target_ratio > 4.0:  #uk
            target_w, target_h = 520, 110
        elif target_ratio > 2.5:  #brbr
            target_w, target_h = 400, 130
        elif target_ratio < 1.5:  #moto
            target_w, target_h = 200, 160
        else:  #us
            target_w, target_h = 300, 150
        
        dst_points = np.array([
            [0, 0], [target_w-1, 0], 
            [target_w-1, target_h-1], [0, target_h-1]
        ], dtype="float32")
        
        try:
            M = cv2.getPerspectiveTransform(quad.astype("float32"), dst_points)
            warped = cv2.warpPerspective(bgr, M, (target_w, target_h))
            return cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
        except:
            return np.zeros((target_h, target_w, 3), dtype=np.uint8)

    @staticmethod
    def executar(contornos, imagem_bgr):
        H, W = imagem_bgr.shape[:2]
        candidatos = []
        
        print(f"[DEBUG] Processando {len(contornos)} contornos")
        
        #1 = haar cascade
        gray = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2GRAY)
        try:
            cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_russian_plate_number.xml")
            if not cascade.empty():
                detections = cascade.detectMultiScale(
                    gray, 
                    scaleFactor=1.05,  # mais sensivel
                    minNeighbors=3,    # menos restritivo
                    minSize=(40, 15),  # menor tamanho mínimo
                    maxSize=(int(W*0.8), int(H*0.3))
                )
                
                print(f"[DEBUG] Haar detectou {len(detections)} regiões")
                
                for (x, y, w, h) in detections:
                    ratio = w / float(h)
                    pattern, ar_score = FiltrarContornos.faixa(ratio)
                    
                    if pattern is None:
                        continue
                    
                    #criar quad retangular
                    quad = np.array([[x,y], [x+w,y], [x+w,y+h], [x,y+h]], dtype="float32")
                    
                    #analise de conteúdo
                    warp_rgb = FiltrarContornos.warpProjetado(imagem_bgr, quad, ratio)
                    text_score = FiltrarContornos.calculoTexto(warp_rgb)

                    #scores de posição e área
                    pos_score = min(1.0, (y + h/2) / H)
                    area_score = min(1.0, (w*h) / (H*W) * 20)
                    
                    final_score = (
                        ar_score * 2.0 +      # Aspect ratio mais importante
                        text_score * 2.5 +    # Densidade de texto muito importante
                        pos_score * 0.3 +     # Posição menos importante
                        area_score * 0.2      # Área menos importante
                    )
                    
                    candidatos.append({
                        "box": (int(x), int(y), int(w), int(h)),
                        "quad": quad,
                        "pattern": pattern,
                        "score": float(final_score),
                        "method": "haar",
                        "ar_score": ar_score,
                        "text_score": text_score
                    })
        except Exception as e:
            print(f"[WARNING] Erro no Haar Cascade: {e}")
        
        #2= analise de contornos
        contornos_validos = 0
        for i, contour in enumerate(contornos):
            # Validação geométrica inicial
            is_valid, reason = FiltrarContornos.validacaoGeometrica(contour, imagem_bgr.shape)
            if not is_valid:
                continue
            
            contornos_validos += 1
            
            peri = cv2.arcLength(contour, True)
            quad_approx = None
            
            for epsilon_factor in [0.02, 0.03, 0.05, 0.08, 0.1]:
                approx = cv2.approxPolyDP(contour, epsilon_factor * peri, True)
                if len(approx) == 4:
                    quad_approx = approx
                    break
            
            if quad_approx is None:
                rect = cv2.minAreaRect(contour)
                box_points = cv2.boxPoints(rect)
                quad_approx = box_points.reshape(-1, 1, 2).astype(np.int32)
            
            quad = FiltrarContornos.ordenarPontos(quad_approx.reshape(4, 2).astype("float32"))
            
            ratio, avg_w, avg_h = FiltrarContornos.aspectRatio(quad)
            pattern, ar_score = FiltrarContornos.faixa(ratio)
            
            if pattern is None:
                continue
            
            warp_rgb = FiltrarContornos.warpProjetado(imagem_bgr, quad, ratio)
            text_score = FiltrarContornos.calculoTexto(warp_rgb)
            
            area_contour = cv2.contourArea(contour)
            area_quad = avg_w * avg_h
            solidity = area_contour / max(area_quad, 1e-6)
            
            y_center = quad[:, 1].mean()
            pos_score = min(1.0, y_center / H)
            
            final_score = (
                ar_score * 1.5 +
                text_score * 2.0 +
                solidity * 0.8 +
                pos_score * 0.3 +
                min(1.0, area_quad / (H*W) * 15) * 0.4
            )
            
            x_min, y_min = int(quad[:, 0].min()), int(quad[:, 1].min())
            x_max, y_max = int(quad[:, 0].max()), int(quad[:, 1].max())
            
            candidatos.append({
                "box": (x_min, y_min, x_max - x_min, y_max - y_min),
                "quad": quad,
                "pattern": pattern,
                "score": float(final_score),
                "method": "contour",
                "ar_score": ar_score,
                "text_score": text_score,
                "solidity": solidity
            })
        
        print(f"[DEBUG] {contornos_validos} contornos passaram na validação inicial")
        print(f"[DEBUG] {len(candidatos)} candidatos finais")
        
        candidatos.sort(key=lambda c: c["score"], reverse=True)
        
        for i, cand in enumerate(candidatos[:3]):
            print(f"[DEBUG] Candidato {i+1}: {cand['pattern']} | Score: {cand['score']:.3f} | "
                  f"AR: {cand['ar_score']:.3f} | Text: {cand['text_score']:.3f} | "
                  f"Método: {cand['method']}")
        
        return candidatos