# evaluate_full_pipeline.py

import argparse
import time
import random
from pathlib import Path
import cv2
import numpy as np
from multiprocessing import Pool, cpu_count
from tqdm import tqdm

# Importa todos os serviços necessários para o pipeline completo
from src.services.preprocessamento import Preprocessamento
from src.services.bordas import Bordas
from src.services.contornos import Contornos
from src.services.filtrarContornos import FiltrarContornos
from src.services.recorte import Recorte
from src.services.ocr import OCR
from src.services.montagem import Montagem
from src.services.validacao import Validacao

def parse_ground_truth_text(txt_path: Path) -> str | None:
    """
    Lê o arquivo .txt e extrai o texto da placa.
    Procura por uma linha que comece com "Plate:" (case-insensitive).
    """
    if not txt_path.exists():
        return None
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.lower().strip().startswith('plate:'):
                return line.split(':', 1)[1].strip().upper()
    return None

def process_single_image_e2e(img_path: Path) -> dict:
    """
    Executa o pipeline completo de ponta a ponta para uma única imagem.
    """
    txt_path = img_path.with_suffix('.txt')
    ground_truth_text = parse_ground_truth_text(txt_path)
    if ground_truth_text is None:
        return {"status": "no_ground_truth", "arquivo": img_path.name}

    try:
        # --- ETAPA 1: DETECÇÃO E RECORTE ---
        img_bgr = cv2.imread(str(img_path))
        if img_bgr is None:
            return {"status": "read_error", "arquivo": img_path.name}

        preproc = Preprocessamento.executar(img_bgr)
        canny_presets = [(50, 150), (100, 200), (150, 250)]
        todos_os_contornos = []
        for (t1, t2) in canny_presets:
            edges = Bordas.executar(preproc, threshold1=t1, threshold2=t2)
            contours = Contornos.executar(edges)
            todos_os_contornos.extend(contours)

        candidatos = FiltrarContornos.executar(todos_os_contornos, img_bgr)
        if not candidatos:
            return {"status": "detection_failed", "arquivo": img_path.name, "ground_truth": ground_truth_text}

        best_candidate = candidatos[0]
        crop_bgr = Recorte.executar(img_bgr, best_candidate.get("quad"))

        # --- ETAPA 2: OCR E VALIDAÇÃO (USANDO O CROP COLORIDO) ---
        texto_ocr, _ = OCR.executarImg(crop_bgr)
        montagem_final = Montagem.executar(texto_ocr)
        valid_plates = Validacao.executar(montagem_final) # Retorna uma lista de possibilidades

        if not valid_plates:
            return {"status": "ocr_failed", "arquivo": img_path.name, "predicted": montagem_final, "ground_truth": ground_truth_text}

        # Verifica se o texto correto está entre as placas validadas
        predicted_texts = [p[0] for p in valid_plates]
        if ground_truth_text in predicted_texts:
            return {"status": "correct", "arquivo": img_path.name, "predicted": ground_truth_text, "ground_truth": ground_truth_text}
        else:
            return {"status": "incorrect", "arquivo": img_path.name, "predicted": predicted_texts[0], "ground_truth": ground_truth_text}

    except Exception as e:
        return {"status": "critical_error", "arquivo": img_path.name, "error": str(e)}


def run_full_pipeline_evaluation(args):
    print("--- Iniciando Avaliação de Pipeline Completo (End-to-End) ---")
    dataset_dir = Path(args.dataset_path)
    
    image_files = list(dataset_dir.glob('*.jpg')) + list(dataset_dir.glob('*.jpeg')) + list(dataset_dir.glob('*.png'))

    if args.random:
        print(f"Executando teste em uma amostra aleatória de {args.random} imagens...")
        image_files = random.sample(image_files, min(args.random, len(image_files)))

    total_images = len(image_files)
    if total_images == 0:
        print("Nenhuma imagem para processar."); return

    print(f"Total de imagens para processar: {total_images}. Usando {cpu_count()} processadores.")
    start_time = time.time()
    
    results = []
    with Pool(processes=cpu_count()) as pool:
        for result in tqdm(pool.imap_unordered(process_single_image_e2e, image_files), total=total_images, desc="Processando Imagens"):
            results.append(result)

    end_time = time.time()
    total_time = end_time - start_time

    # --- ANÁLISE DOS RESULTADOS ---
    correct_reads = 0
    incorrect_reads = 0
    detection_failures = 0
    ocr_failures = 0
    critical_errors = 0
    error_log = []

    for res in results:
        status = res.get("status")
        if status == "correct":
            correct_reads += 1
        elif status == "incorrect":
            incorrect_reads += 1
            error_log.append(f"Arquivo: {res['arquivo']} | Esperado: {res['ground_truth']} | Lido: {res['predicted']}")
        elif status == "detection_failed":
            detection_failures += 1
            error_log.append(f"Arquivo: {res['arquivo']} | Esperado: {res['ground_truth']} | Erro: Falha na Detecção")
        elif status == "ocr_failed":
            ocr_failures += 1
            error_log.append(f"Arquivo: {res['arquivo']} | Esperado: {res['ground_truth']} | Erro: Falha no OCR/Validação (lido: {res.get('predicted', '')})")
        elif status == "critical_error":
            critical_errors += 1
            error_log.append(f"Arquivo: {res['arquivo']} | Erro Crítico: {res.get('error', 'N/A')}")

    total_processed = len(results)
    accuracy = (correct_reads / total_processed) * 100 if total_processed > 0 else 0

    print("\n\n--- Relatório de Avaliação End-to-End ---")
    print(f"Tempo total: {total_time:.2f} segundos ({total_images / (total_time + 1e-6):.2f} imgs/seg)")
    print(f"Total de imagens processadas: {total_processed}")
    print("-" * 50)
    print(f"Leituras Corretas: {correct_reads} ({accuracy:.2f}%)")
    print("-" * 50)
    print(f"Leituras Incorretas: {incorrect_reads}")
    print(f"Falhas de Detecção (não achou a placa): {detection_failures}")
    print(f"Falhas de OCR/Validação (não leu texto válido): {ocr_failures}")
    print(f"Erros Críticos (crashes no código): {critical_errors}")

    if args.save_log and error_log:
        log_path = Path("relatorio_erros_e2e.txt")
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write("--- Relatório Detalhado de Falhas ---\n\n")
            f.writelines([f"{line}\n" for line in error_log])
        print(f"\n[INFO] Relatório detalhado de erros salvo em: '{log_path}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script para avaliar a precisão do pipeline completo de ALPR.")
    parser.add_argument("dataset_path", help="Caminho para a pasta contendo as imagens e os arquivos .txt. Ex: '/home/rodrigo/Área de Trabalho/fotos_dataset_juntas'")
    parser.add_argument("-r", "--random", type=int, metavar='N', help="Executa o teste em uma amostra de N imagens aleatórias.")
    parser.add_argument("--save-log", action="store_true", help="Salva um relatório detalhado de todas as falhas em um arquivo de texto.")
    
    args = parser.parse_args()
    run_full_pipeline_evaluation(args)