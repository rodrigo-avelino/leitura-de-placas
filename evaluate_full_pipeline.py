# evaluate_full_pipeline.py (Versão 3.3 - Desambiguação Adaptativa com Métricas)

import argparse
import time
import random
from pathlib import Path
import cv2
import numpy as np
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from shapely.geometry import Polygon
import functools
# import logging  # REMOVIDO
# import sys      # REMOVIDO

# Importa todos os serviços necessários
from src.services.preprocessamento import Preprocessamento
from src.services.bordas import Bordas
from src.services.contornos import Contornos
from src.services.filtrarContornos import FiltrarContornos
from src.services.recorte import Recorte
from src.services.ocr import OCR
from src.services.montagem import Montagem
from src.services.validacao import Validacao
from src.services.analiseCor import AnaliseCor # <<< Necessário para a desambiguação

# --- (Funções levenshtein_distance, parse_ground_truth, calculate_iou permanecem iguais) ---
def levenshtein_distance(s1: str, s2: str) -> int:
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1): dp[i][0] = i
    for j in range(n + 1): dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    return dp[m][n]

def parse_ground_truth(txt_path: Path) -> dict:
    gt = {"text": None, "quad": None}
    if not txt_path.exists(): return gt
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.lower().strip().startswith('plate:'):
                gt["text"] = line.split(':', 1)[1].strip().upper()
            elif line.lower().startswith('corners:'):
                parts = line.split(':', 1)[1].strip().split()
                if len(parts) == 4:
                    try: gt["quad"] = np.array([p.split(',') for p in parts], dtype=np.float32)
                    except: pass
    return gt

def calculate_iou(quad1: np.ndarray, quad2: np.ndarray) -> float:
    try:
        poly1, poly2 = Polygon(quad1), Polygon(quad2)
        intersection_area = poly1.intersection(poly2).area
        union_area = poly1.union(poly2).area
        return intersection_area / union_area if union_area > 0 else 0.0
    except Exception: return 0.0
# --- FIM DAS FUNÇÕES HELPER ---


def process_single_image_e2e(img_path: Path, iou_threshold: float, blue_threshold: float) -> dict: # Adicionado blue_threshold
    """
    Executa o pipeline completo E REPLICA A LÓGICA DE DECISÃO do placaController.
    """
    # --- REMOVIDO: Configuração de logging ---

    txt_path = img_path.with_suffix('.txt')
    ground_truth = parse_ground_truth(txt_path)
    gt_text = ground_truth.get("text")
    gt_quad = ground_truth.get("quad")

    if gt_text is None or gt_quad is None:
        return {"status": "no_ground_truth", "arquivo": img_path.name}

    result = {
        "status": "detection_failed", "iou_score": 0.0,
        "char_errors": len(gt_text), "gt_chars": len(gt_text),
        "predicted": "", "gt_text": gt_text, "arquivo": img_path.name
    }

    try:
        img_bgr = cv2.imread(str(img_path))
        if img_bgr is None:
            return {**result, "status": "read_error"}

        # --- ETAPA 1: DETECÇÃO E CÁLCULO DE IoU ---
        preproc = Preprocessamento.executar(img_bgr)
        canny_presets = [(50, 150), (100, 200), (150, 250)]
        todos_os_contornos = []
        for (t1, t2) in canny_presets:
            edges = Bordas.executar(preproc, threshold1=t1, threshold2=t2)
            contours = Contornos.executar(edges)
            todos_os_contornos.extend(contours)
        candidatos = FiltrarContornos.executar(todos_os_contornos, img_bgr)
        if not candidatos: return result
        best_candidate = candidatos[0]
        predicted_quad = best_candidate.get("quad")
        result["iou_score"] = calculate_iou(predicted_quad, gt_quad)

        # --- ETAPA 2: RECORTE, OCR E VALIDAÇÃO ---
        crop_bgr = Recorte.executar(img_bgr, predicted_quad)
        texto_ocr, confiancas = OCR.executarImg(crop_bgr)
        montagem_final = Montagem.executar(texto_ocr)
        placas_validas = Validacao.executar(montagem_final, confiancas)

        if not placas_validas:
            result["status"] = "ocr_failed"
            result["predicted"] = montagem_final
            result["char_errors"] = levenshtein_distance(montagem_final, gt_text)
            return result

        # --- LÓGICA DE DESAMBIGUAÇÃO ADAPTATIVA (USANDO METADE SUPERIOR) ---
        analise_cores = AnaliseCor.executar(crop_bgr)
        texto_final = None

        if len(placas_validas) == 1:
            texto_final, _ = placas_validas[0]
        else:
            percent_azul_superior = analise_cores.get("percent_azul_superior", 0)

            # Usa o blue_threshold passado como argumento
            if percent_azul_superior > blue_threshold:
                for placa, padrao in placas_validas:
                    if padrao == "MERCOSUL": texto_final = placa; break
            else:
                for placa, padrao in placas_validas:
                    if padrao == "ANTIGA": texto_final = placa; break

            if not texto_final:
                texto_final, _ = placas_validas[0]

        result["predicted"] = texto_final

        # --- ETAPA 3: CÁLCULO FINAL DAS MÉTRICAS (LÓGICA ESTRITA) ---
        if texto_final == gt_text:
            result["status"] = "correct"
            result["char_errors"] = 0
        else:
            result["status"] = "incorrect"
            result["char_errors"] = levenshtein_distance(texto_final, gt_text)

        return result

    except Exception as e:
        # Imprime erros críticos no stderr
        # import sys # Descomente se sys não estiver importado globalmente
        # print(f"ERRO CRÍTICO no arquivo {img_path.name}: {e}", file=sys.stderr)
        return {**result, "status": "critical_error", "error": str(e)}

# --- (Função run_full_pipeline_evaluation permanece a mesma da v3.3/v3.7) ---
def run_full_pipeline_evaluation(args):
    print("--- Iniciando Avaliação de Pipeline Completo (Métricas Avançadas) ---")
    print(f"[INFO] Usando Blue Threshold: {args.blue_threshold:.2f}") # Informa o threshold usado
    dataset_dir = Path(args.dataset_path)
    image_files = list(dataset_dir.glob('*.jpg')) + list(dataset_dir.glob('*.jpeg')) + list(dataset_dir.glob('*.png'))
    if args.random:
        print(f"Executando teste em uma amostra aleatória de {args.random} imagens...")
        image_files = random.sample(image_files, min(args.random, len(image_files)))
    total_images = len(image_files)
    if total_images == 0: print("Nenhuma imagem para processar."); return
    print(f"Total de imagens para processar: {total_images}. Usando {cpu_count()} processadores.")
    start_time = time.time()

    # Passa o blue_threshold para a função de processamento
    partial_process_func = functools.partial(process_single_image_e2e,
                                             iou_threshold=args.iou_threshold,
                                             blue_threshold=args.blue_threshold)
    results = []
    with Pool(processes=cpu_count()) as pool:
        for result in tqdm(pool.imap_unordered(partial_process_func, image_files), total=total_images, desc="Processando Imagens"):
            results.append(result)
    end_time = time.time()
    total_time = end_time - start_time
    total_processed = len(results)

    # --- (A parte de análise e exibição de métricas permanece idêntica) ---
    latency_avg = total_time / total_processed if total_processed > 0 else 0
    throughput_fps = total_processed / total_time if total_time > 0 else 0
    correct_reads, correct_detections_iou = 0, 0
    total_char_errors, total_gt_chars = 0, 0
    status_counts = {"correct": 0, "incorrect": 0, "detection_failed": 0, "ocr_failed": 0, "critical_error": 0, "no_ground_truth": 0, "read_error": 0}
    error_log = []
    for res in results:
        status = res.get("status")
        status_counts[status] += 1
        if status not in ["no_ground_truth", "read_error"]:
            if res.get("iou_score", 0.0) >= args.iou_threshold: correct_detections_iou += 1
            if status == "correct": correct_reads += 1
            total_char_errors += res.get("char_errors", 0)
            total_gt_chars += res.get("gt_chars", 0)
            if status not in ["correct", "critical_error"]:
                error_log.append(f"Arquivo: {res['arquivo']} | Status: {status} | Esperado: {res['gt_text']} | Lido: {res.get('predicted', 'N/A')}")
            elif status == "critical_error":
                 error_log.append(f"Arquivo: {res['arquivo']} | Status: {status} | Erro: {res.get('error')}")
    e2e_accuracy = (correct_reads / total_processed) * 100 if total_processed > 0 else 0
    detection_accuracy_iou = (correct_detections_iou / total_processed) * 100 if total_processed > 0 else 0
    character_error_rate_cer = (total_char_errors / total_gt_chars) * 100 if total_gt_chars > 0 else 0
    print("\n\n--- Relatório de Métricas de Desempenho (Velocidade) ---")
    print(f"Total de imagens processadas: {total_processed}")
    print(f"Tempo total de processamento: {total_time:.2f} segundos")
    print(f"1.1. Latência Média por Imagem: {latency_avg:.4f} segundos/imagem")
    print(f"1.2. Frames Por Segundo (FPS): {throughput_fps:.2f} FPS")
    print("\n--- Relatório de Métricas de Precisão (Qualidade) ---")
    print(f"2.1. Acurácia End-to-End: {correct_reads}/{total_processed} ({e2e_accuracy:.2f}%)")
    print(f"2.2. Acurácia da Detecção (IoU >= {args.iou_threshold}): {correct_detections_iou}/{total_processed} ({detection_accuracy_iou:.2f}%)")
    print(f"3.3. Taxa de Erro por Caractere (CER): {total_char_errors}/{total_gt_chars} erros ({character_error_rate_cer:.2f}%)")
    print("\n--- Detalhamento das Falhas ---")
    print(f"Leituras Incorretas (achou, mas leu errado): {status_counts['incorrect']}")
    print(f"Falhas de Detecção (não achou placa): {status_counts['detection_failed']}")
    print(f"Falhas de OCR/Validação (achou, mas não leu texto válido): {status_counts['ocr_failed']}")
    print(f"Erros Críticos (crashes no código): {status_counts['critical_error']}")
    print(f"Imagens ignoradas (sem gabarito/erro de leitura): {status_counts['no_ground_truth'] + status_counts['read_error']}")
    if args.save_log and error_log:
        log_path = Path(f"relatorio_erros_metricas_e2e_blue_{args.blue_threshold:.2f}.txt") # Nome do log inclui o threshold
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"--- Relatório Detalhado de Falhas (Blue Threshold: {args.blue_threshold:.2f}) ---\n\n")
            f.writelines([f"{line}\n" for line in error_log])
        print(f"\n[INFO] Relatório detalhado de erros salvo em: '{log_path}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script para avaliar a precisão do pipeline completo de ALPR.")
    parser.add_argument("dataset_path", help="Caminho para a pasta contendo as imagens e os arquivos .txt.")
    parser.add_argument("--iou_threshold", type=float, default=0.1, help="Limiar de IoU para detecção correta. Padrão: 0.1")
    # NOVO ARGUMENTO para testar o limiar de azul
    parser.add_argument("--blue_threshold", type=float, default=0.10, help="Limiar de percentual azul na metade superior para classificar como Mercosul. Padrão: 0.10")
    parser.add_argument("-r", "--random", type=int, metavar='N', help="Executa o teste em N imagens aleatórias.")
    parser.add_argument("--save-log", action="store_true", help="Salva um relatório detalhado das falhas.")
    args = parser.parse_args()
    if args.iou_threshold != 0.1: print(f"[INFO] Usando IoU Threshold: {args.iou_threshold}")
    else: print(f"[INFO] Usando IoU Threshold padrão otimizado: 0.1")
    run_full_pipeline_evaluation(args)