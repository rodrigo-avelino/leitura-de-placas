import cv2
import numpy as np

# Padrões de aspecto (largura/altura) típicos para diferentes formatos de placa.
# Cada item = (aspect_ratio_ideal, tolerância_relativa)
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
        """
        Recebe o aspect ratio medido de um candidato e retorna:
          - o nome do padrão mais próximo (dentro da tolerância)
          - um score (0..0.9) proporcional à proximidade do ratio ideal

        Se nada estiver dentro da tolerância, retorna (None, 0.0).
        """
        best_name, best_score = None, 0.0
        
        for name, (ideal, tol) in ASPECT_PATTERNS.items():
            # Diferença relativa entre o ratio medido e o ideal
            diff = abs(ratio - ideal) / ideal
            
            # Considera apenas se estiver dentro da faixa de tolerância
            if diff <= tol:
                # Score cresce quanto menor for a diferença relativa
                score = (1.0 - (diff / tol)) * 0.9
                if score > best_score:
                    best_name, best_score = name, score
        
        return best_name, best_score

    @staticmethod
    def ordenarPontos(pts):
        """
        Ordena 4 pontos de um quadrilátero na convenção:
          rect[0]=top-left, rect[1]=top-right, rect[2]=bottom-right, rect[3]=bottom-left

        Baseia-se na soma e diferença das coordenadas para inferir as posições.
        """
        rect = np.zeros((4, 2), dtype="float32")
        
        # Menor soma -> top-left | Maior soma -> bottom-right
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        
        # Menor diferença -> top-right | Maior diferença -> bottom-left
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        return rect

    @staticmethod
    def aspectRatio(quad):
        """
        Calcula o aspect ratio médio (largura/altura) de um quadrilátero,
        usando a média das duas larguras e das duas alturas opostas.
        Retorna (ratio, avg_width, avg_height).
        """
        (tl, tr, br, bl) = quad
        
        # Larguras (topo e base)
        width_top = np.linalg.norm(tr - tl)
        width_bottom = np.linalg.norm(br - bl)
        
        # Alturas (esquerda e direita)
        height_left = np.linalg.norm(bl - tl)
        height_right = np.linalg.norm(br - tr)
        
        # Médias
        avg_width = (width_top + width_bottom) / 2.0
        avg_height = (height_left + height_right) / 2.0
        
        # Evita divisão por zero com max(..., 1e-6)
        return avg_width / max(avg_height, 1e-6), avg_width, avg_height

    @staticmethod
    def calculoTexto(warp_rgb):
        """
        Estima um 'score de texto' (0..1) no warp da placa:
          1) Converte para cinza
          2) Binariza adaptativamente (destaca caracteres)
          3) Conta componentes conexos dentro de faixas plausíveis de área e aspect ratio
          4) Normaliza a contagem assumindo ~7 caracteres como 'cheio' (score=1)
        """
        gray = cv2.cvtColor(warp_rgb, cv2.COLOR_RGB2GRAY)
        
        # Binarização que tende a separar letras/números do fundo
        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Inverte (255 - binary) para que caracteres (escuros) virem blobs brancos
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(255 - binary)
        
        # Conta componentes plausíveis como caracteres
        char_count = 0
        h, w = gray.shape
        min_char_area = (h * w) * 0.01  # mínimo ~1% da área
        max_char_area = (h * w) * 0.25  # máximo ~25% da área
        
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if min_char_area <= area <= max_char_area:
                comp_w = stats[i, cv2.CC_STAT_WIDTH]
                comp_h = stats[i, cv2.CC_STAT_HEIGHT]
                if comp_h > 0:
                    comp_ratio = comp_w / comp_h
                    # Faixa genérica para formas de caracteres
                    if 0.3 <= comp_ratio <= 2.0:
                        char_count += 1
        
        # Normaliza pela quantidade típica de caracteres (7)
        return min(1.0, char_count / 7.0)

    @staticmethod
    def validacaoGeometrica(contour, image_shape):
        """
        Faz filtros geométricos rápidos para descartar contornos ruins:
          - área mínima/máxima relativa ao frame
          - dimensões mínimas do bounding box
          - margem contra bordas da imagem
          - aspect ratio básico do bounding box
        Retorna (True/False, motivo).
        """
        H, W = image_shape[:2]
        
        # Área do contorno deve estar numa faixa razoável
        area = cv2.contourArea(contour)
        min_area = 0.003 * H * W  # permite placas menores/distantes
        max_area = 0.25 * H * W   # evita candidatos muito grandes
        
        if area < min_area or area > max_area:
            return False, "area_invalid"
        
        # Bounding box do contorno
        x, y, w, h = cv2.boundingRect(contour)
        
        # Dimensões mínimas (evita ruído)
        if w < 50 or h < 15:
            return False, "too_small"
    
        # Reprova candidatos colados nas bordas
        margin = min(20, min(W, H) * 0.02)
        if (x < margin or y < margin or 
            (x + w) > (W - margin) or (y + h) > (H - margin)):
            return False, "edge_proximity"
        
        # Aspect ratio simples do retângulo do contorno
        basic_ratio = w / h
        if basic_ratio < 0.8 or basic_ratio > 6.0:
            return False, "basic_ratio"
        
        return True, "valid"

    @staticmethod
    def warpProjetado(bgr, quad, target_ratio):
        """
        Faz a transformação de perspectiva do quadrilátero 'quad' para um retângulo
        de tamanho fixo ('target_w' x 'target_h'), com heurística baseada no aspect ratio
        estimado (para escolher resolução de saída).
        Retorna a imagem warpada em RGB.
        """
        # Heurística de dimensões-alvo por tipo de placa
        if target_ratio > 4.0:          # ex.: placas mais compridas (EU/UK)
            target_w, target_h = 520, 110
        elif target_ratio > 2.5:        # ex.: BR carro (antiga/mercosul)
            target_w, target_h = 400, 130
        elif target_ratio < 1.5:        # ex.: placa de moto (mais "alta")
            target_w, target_h = 200, 160
        else:                           # ex.: padrão US genérico
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
            # Em caso de falha, devolve "canvas" vazio do tamanho esperado
            return np.zeros((target_h, target_w, 3), dtype=np.uint8)

    # Cole esta nova função dentro da classe FiltrarContornos
    # Cole esta nova função no lugar da antiga _encolher_quad
    @staticmethod
    def _encolher_quad(quad, fator_encolhimento=0.03, max_shrink_ratio=0.15):
        """
        Encolhe (move para dentro) os 4 vértices de um quadrilátero em direção ao centro,
        para reduzir margens externas (parafusos/bordas) e focar nos caracteres.

        Segurança:
          - Limita o quanto cada ponto pode se mover a 15% da altura média do quad,
            evitando "comer" demais a área útil.

        Parâmetros:
          fator_encolhimento: fração do vetor (vértice->centro) a aplicar.
          max_shrink_ratio: fração máxima da altura média permitida como deslocamento.
        """
        if quad is None:
            return None

        # Altura média (usada para limitar deslocamento máximo)
        (tl, tr, br, bl) = quad
        height_left  = np.linalg.norm(bl - tl)
        height_right = np.linalg.norm(br - tr)
        avg_height = (height_left + height_right) / 2.0

        limite_movimento_px = avg_height * max_shrink_ratio

        centroide = quad.mean(axis=0)
        quad_encolhido = np.zeros_like(quad)

        for i in range(4):
            vetor = quad[i] - centroide  # direção do vértice até o centro
            # Posição sugerida com o fator informado
            ponto_proposto = quad[i] - (vetor * fator_encolhimento)

            # Distância do movimento sugerido
            distancia_movimento = np.linalg.norm(ponto_proposto - quad[i])

            if distancia_movimento > limite_movimento_px:
                # Se excedeu o limite, move apenas até o limite mantendo a direção
                vetor_unitario = vetor / np.linalg.norm(vetor)
                quad_encolhido[i] = quad[i] - (vetor_unitario * limite_movimento_px)
            else:
                # Movimento dentro do limite: aplica o sugerido
                quad_encolhido[i] = ponto_proposto

        return quad_encolhido.astype(np.float32)

    @staticmethod
    def executar(contornos, imagem_bgr):
        """
        Recebe a lista de contornos e a imagem original BGR.
        Produz uma lista de 'candidatos' de placa com scores agregados, contendo:
          - box: bounding box axis-aligned
          - quad: 4 pontos (float32) ordenados (TL, TR, BR, BL)
          - pattern: rótulo do padrão de plate (ex.: BR_carro_mercosul)
          - score: confiança agregada (aspecto, texto, posição, área/solidez)
          - method: origem do candidato (haar | contour)
          - métricas auxiliares (ar_score, text_score, solidity, etc.)

        Fluxo:
          1) (Opcional) Haar cascade em escala de cinza -> candidatos retangulares
          2) Loop nos contornos -> validação geométrica -> aproxima quadrilátero
          3) Warping + análise de texto + métricas -> score final
          4) Ordena por score e aplica refinamento (_encolher_quad) no melhor
        """
        H, W = imagem_bgr.shape[:2]
        candidatos = []
        
        print(f"[DEBUG] Processando {len(contornos)} contornos")
        
        # ---------- (1) CANDIDATOS VIA HAAR CASCADE (opcional/auxiliar) ----------
        gray = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2GRAY)
        try:
            cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_russian_plate_number.xml")
            if not cascade.empty():
                detections = cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.05,   # sensível
                    minNeighbors=3,     # menos restritivo
                    minSize=(40, 15),   # tamanho mínimo
                    maxSize=(int(W*0.8), int(H*0.3))
                )
                
                print(f"[DEBUG] Haar detectou {len(detections)} regiões")
                
                for (x, y, w, h) in detections:
                    ratio = w / float(h)
                    pattern, ar_score = FiltrarContornos.faixa(ratio)
                    if pattern is None:
                        continue
                    
                    # Cria quad retangular a partir da detecção (eixo alinhado)
                    quad = np.array([
                        [x, y], [x+w, y],
                        [x+w, y+h], [x, y+h]
                    ], dtype="float32")
                    
                    # Warping + score de "densidade de texto"
                    warp_rgb = FiltrarContornos.warpProjetado(imagem_bgr, quad, ratio)
                    text_score = FiltrarContornos.calculoTexto(warp_rgb)

                    # Heurísticas simples de posição/área para compor score
                    pos_score = min(1.0, (y + h/2) / H)                # placas tendem a ficar na metade inferior
                    area_score = min(1.0, (w*h) / (H*W) * 20)          # privilegia caixas com área razoável
                    
                    final_score = (
                        ar_score   * 2.0  +   # peso forte para aspecto
                        text_score * 2.5  +   # texto é muito importante
                        pos_score  * 0.3  +
                        area_score * 0.2
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
            # Falha na carga/execução do cascade não interrompe o pipeline
            print(f"[WARNING] Erro no Haar Cascade: {e}")
        
        # ---------- (2) CANDIDATOS VIA ANÁLISE DE CONTORNOS ----------
        contornos_validos = 0
        for i, contour in enumerate(contornos):
            # Filtragem geométrica grosseira
            is_valid, reason = FiltrarContornos.validacaoGeometrica(contour, imagem_bgr.shape)
            if not is_valid:
                continue
            contornos_validos += 1
            
            # Aproxima contorno a um polígono; tenta achar 4 vértices
            peri = cv2.arcLength(contour, True)
            quad_approx = None
            for epsilon_factor in [0.02, 0.03, 0.05, 0.08, 0.1]:
                approx = cv2.approxPolyDP(contour, epsilon_factor * peri, True)
                if len(approx) == 4:
                    quad_approx = approx
                    break
            
            # Se não achou 4 pontos, usa o retângulo mínimo orientado (minAreaRect)
            if quad_approx is None:
                rect = cv2.minAreaRect(contour)
                box_points = cv2.boxPoints(rect)
                quad_approx = box_points.reshape(-1, 1, 2).astype(np.int32)
            
            # Ordena pontos (TL, TR, BR, BL)
            quad = FiltrarContornos.ordenarPontos(quad_approx.reshape(4, 2).astype("float32"))
            
            # Aspect ratio médio + largura/altura médias
            ratio, avg_w, avg_h = FiltrarContornos.aspectRatio(quad)
            pattern, ar_score = FiltrarContornos.faixa(ratio)
            if pattern is None:
                continue
            
            # Warping para retângulo e análise do "texto"
            warp_rgb = FiltrarContornos.warpProjetado(imagem_bgr, quad, ratio)
            text_score = FiltrarContornos.calculoTexto(warp_rgb)
            
            # Métricas auxiliares:
            area_contour = cv2.contourArea(contour)
            area_quad = avg_w * avg_h
            solidity = area_contour / max(area_quad, 1e-6)   # quão "cheio" o contorno é
            y_center = quad[:, 1].mean()
            pos_score = min(1.0, y_center / H)               # placas tendem a estar da metade pra baixo
            
            # Score final (pesos ajustados empiricamente)
            final_score = (
                ar_score * 1.5 +
                text_score * 2.0 +
                solidity  * 0.8 +
                pos_score * 0.3 +
                min(1.0, area_quad / (H*W) * 15) * 0.4
            )
            
            # Bounding box axis-aligned do quad (útil para debug/visualização)
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
        
        # Ordena todos (haar + contorno) do melhor pro pior
        candidatos.sort(key=lambda c: c["score"], reverse=True)

        # ---------- (3) NOVO REFINAMENTO: ENCOLHER O MELHOR QUAD ----------
        # Objetivo: reduzir bordas/molduras e focar nos caracteres (melhora OCR).
        if candidatos:
            melhor_candidato = candidatos[0]
            quad_original = melhor_candidato.get("quad")
            quad_refinado = FiltrarContornos._encolher_quad(
                quad_original,
                fator_encolhimento=0.25  # encolhe 25% do vetor até o centro (com trava)
            )
            melhor_candidato["quad"] = quad_refinado
        
        # Log de debug dos top-3 candidatos
        for i, cand in enumerate(candidatos[:3]):
            print(
                f"[DEBUG] Candidato {i+1}: {cand['pattern']} | "
                f"Score: {cand['score']:.3f} | AR: {cand['ar_score']:.3f} | "
                f"Text: {cand['text_score']:.3f} | Método: {cand['method']}"
            )
        
        return candidatos
