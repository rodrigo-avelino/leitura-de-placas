# evaluate_crop.py (VERSÃO FINAL COM A/B TESTING)
import argparse
import time
import random
from pathlib import Path
import cv2
import numpy as np
from shapely.geometry import Polygon
from multiprocessing import Pool, cpu_count
from tqdm import tqdm

from src.services.preprocessamento import Preprocessamento
from src.services.bordas import Bordas
from src.services.contornos import Contornos
from src.services.filtrarContornos import FiltrarContornos

# ... (funções parse_ground_truth_quad, calculate_iou, process_single_image permanecem iguais) ...
def parse_ground_truth_quad(txt_path: Path) -> np.ndarray | None:
    if not txt_path.exists(): return None
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.lower().startswith('corners:'):
                parts = line.split(':', 1)[1].strip().split()
                if len(parts) == 4:
                    try: return np.array([p.split(',') for p in parts], dtype=np.float32)
                    except: return None
    return None

def calculate_iou(quad1: np.ndarray, quad2: np.ndarray) -> float:
    try:
        poly1, poly2 = Polygon(quad1), Polygon(quad2)
        intersection_area = poly1.intersection(poly2).area
        union_area = poly1.union(poly2).area
        return intersection_area / union_area if union_area > 0 else 0.0
    except Exception: return 0.0

def process_single_image(img_path: Path) -> dict:
    txt_path = img_path.with_suffix('.txt')
    gt_quad = parse_ground_truth_quad(txt_path)
    if gt_quad is None: return {"status": "no_ground_truth"}
    try:
        img_bgr = cv2.imread(str(img_path))
        if img_bgr is None: return {"status": "read_error", "arquivo": img_path.name}
        preproc = Preprocessamento.executar(img_bgr)
        canny_presets = [(50, 150), (100, 200), (150, 250)]
        todos_os_contornos = []
        for (t1, t2) in canny_presets:
            edges = Bordas.executar(preproc, threshold1=t1, threshold2=t2)
            contours = Contornos.executar(edges)
            todos_os_contornos.extend(contours)
        candidatos = FiltrarContornos.executar(todos_os_contornos, img_bgr)
        if not candidatos or not candidatos[0].get('score') or candidatos[0]['score'] == 0:
            return {"status": "failed_detection"}
        best_candidate = candidatos[0]
        predicted_quad = best_candidate.get("quad")
        if predicted_quad is None: return {"status": "failed_detection"}
        iou = calculate_iou(predicted_quad, gt_quad)
        return {"status": "processed", "iou_score": iou, "arquivo": img_path.name, "method": best_candidate.get("method", "unknown")}
    except Exception as e: return {"status": "critical_error", "arquivo": img_path.name, "error": str(e)}

def run_crop_evaluation(args):
    print("--- Iniciando Avaliação de Recorte (Crop) ---")
    dataset_dir = Path(args.dataset_path)
    
    # LÓGICA DE SELEÇÃO DE ARQUIVOS ATUALIZADA
    if args.load_file_list:
        file_list_path = Path(args.load_file_list)
        if not file_list_path.exists():
            print(f"ERRO: A lista de arquivos '{file_list_path}' não foi encontrada.")
            return
        print(f"Carregando lista de imagens de '{file_list_path}'...")
        with open(file_list_path, 'r') as f:
            # Garante que os caminhos sejam absolutos a partir do dataset_path
            image_files = [dataset_dir / fname.strip() for fname in f.readlines()]
    else:
        image_files = list(dataset_dir.glob('*.jpg')) + list(dataset_dir.glob('*.jpeg')) + list(dataset_dir.glob('*.png'))

    if args.worst:
        report_to_read = Path("relatorio_erros_recorte.txt")
        if not report_to_read.exists():
            print(f"ERRO: Arquivo de relatório '{report_to_read}' não encontrado.")
            return
        print(f"Executando teste nas {args.worst} piores imagens de '{report_to_read}'...")
        worst_files = [line.split('|')[0].strip() for line in open(report_to_read, 'r', encoding='utf-8') if '|' in line and 'Arquivo' not in line]
        worst_files_subset = worst_files[:args.worst]
        file_map = {p.name: p for p in image_files}
        image_files = [file_map[fname] for fname in worst_files_subset if fname in file_map]

    elif args.random:
        print(f"Executando teste em uma amostra aleatória de {args.random} imagens...")
        image_files = random.sample(image_files, min(args.random, len(image_files)))

    # NOVO: Salva a lista de arquivos, se solicitado
    if args.save_file_list:
        file_list_path = Path(args.save_file_list)
        print(f"Salvando a lista de {len(image_files)} imagens em '{file_list_path}'...")
        with open(file_list_path, 'w') as f:
            f.writelines([f"{p.name}\n" for p in image_files])
            
    # O resto do código continua igual...
    total_images = len(image_files)
    if total_images == 0: print("Nenhuma imagem para processar."); return
    print(f"Total de imagens para processar: {total_images}. Usando {cpu_count()} processadores.")
    start_time = time.time()
    results = []
    with Pool(processes=cpu_count()) as pool:
        for result in tqdm(pool.imap_unordered(process_single_image, image_files), total=total_images, desc="Processando Imagens"):
            results.append(result)
    # ... (toda a lógica de relatório permanece a mesma)
    end_time = time.time()
    total_time = end_time - start_time; successful_crops = 0; failed_detections = 0; localization_failures = []; critical_errors = []; haar_success_count = 0; contour_success_count = 0
    for res in results:
        status = res.get("status")
        if status == "processed":
            if res["iou_score"] >= args.iou_threshold:
                successful_crops += 1
                if res["method"] == "haar": haar_success_count += 1
                elif res["method"] == "contour": contour_success_count += 1
            else: localization_failures.append(res)
        elif status == "failed_detection": failed_detections += 1
        elif status == "critical_error": critical_errors.append(res)
    print(f"\n\n--- Relatório de Avaliação da Detecção/Recorte ---")
    print(f"Tempo total: {total_time:.2f} segundos ({total_images / (total_time + 1e-6):.2f} imgs/seg)")
    print(f"Total de imagens válidas: {len(results)}")
    print("-" * 50)
    accuracy = (successful_crops / len(results)) * 100 if results else 0; detection_failure_rate = (failed_detections / len(results)) * 100 if results else 0; localization_failure_rate = (len(localization_failures) / len(results)) * 100 if results else 0; error_rate = (len(critical_errors) / len(results)) * 100 if results else 0
    print(f"Recortes Corretos (IoU >= {args.iou_threshold}): {successful_crops} ({accuracy:.2f}%)")
    print(f"  - Encontrados por Haar: {haar_success_count}"); print(f"  - Encontrados por Contorno: {contour_success_count}")
    print(f"Falhas de Detecção (não achou placa): {failed_detections} ({detection_failure_rate:.2f}%)"); print(f"Falhas de Localização (achou no lugar errado): {len(localization_failures)} ({localization_failure_rate:.2f}%)"); print(f"Erros Críticos (crashes no código): {len(critical_errors)} ({error_rate:.2f}%)")
    report_path = Path(f"relatorio_erros_recorte{args.output_suffix}.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("--- Relatório Detalhado de Falhas de Localização ---\n\n");
        if not localization_failures: f.write("Nenhuma falha de localização encontrada.\n")
        else:
            f.write(f"{'Arquivo':<25} | {'Score IoU'}\n"); f.write("-" * 40 + "\n")
            valid_failures = [fail for fail in localization_failures if 'iou_score' in fail]
            for fail in sorted(valid_failures, key=lambda x: x["iou_score"]): f.write(f"{fail['arquivo']:<25} | {fail['iou_score']:.3f}\n")
    print(f"\n[INFO] Relatório detalhado salvo em: '{report_path}'")
    if critical_errors:
        error_report_path = Path(f"relatorio_erros_criticos{args.output_suffix}.txt")
        with open(error_report_path, 'w', encoding='utf-8') as f:
            f.write("--- Relatório de Erros Críticos de Execução ---\n\n")
            for err in critical_errors: f.write(f"Arquivo: {err['arquivo']}\nErro: {err['error']}\n---\n")
        print(f"[AVISO] Relatório de erros críticos salvo em: '{error_report_path}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script para avaliar a precisão da etapa de recorte de placa.")
    parser.add_argument("dataset_path", help="Caminho para a pasta contendo as imagens.")
    parser.add_argument("--iou_threshold", type=float, default=0.5)
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument("-r", "--random", type=int, metavar='N', help="Executa o teste em N imagens aleatórias.")
    test_group.add_argument("-w", "--worst", type=int, metavar='N', help="Executa o teste nas N piores imagens do último relatório.")
    # NOVOS ARGUMENTOS PARA A/B TESTING
    parser.add_argument("--save-file-list", type=str, metavar='PATH', help="Salva a lista de arquivos processados em PATH.")
    parser.add_argument("--load-file-list", type=str, metavar='PATH', help="Carrega e processa uma lista de arquivos de PATH.")
    
    parser.add_argument("-o", "--output-suffix", type=str, default="", help="Sufixo para os arquivos de relatório (ex: '_teste1').")
    args = parser.parse_args()
    run_crop_evaluation(args)