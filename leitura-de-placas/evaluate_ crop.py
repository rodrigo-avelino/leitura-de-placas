import argparse
import time
from pathlib import Path
import cv2
import numpy as np
from shapely.geometry import Polygon

# Importa os serviços necessários para a DETECÇÃO da placa
from src.services.preprocessamento import Preprocessamento
from src.services.bordas import Bordas
from src.services.contornos import Contornos
from src.services.filtrarContornos import FiltrarContornos

def parse_ground_truth_quad(txt_path: Path) -> np.ndarray | None:
    """
    Lê um arquivo .txt e extrai as coordenadas da linha 'corners: ...'.
    Retorna um array numpy de 4x2 pontos.
    """
    if not txt_path.exists():
        return None
    
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.lower().startswith('corners:'):
                parts = line.split(':', 1)[1].strip().split()
                if len(parts) == 4:
                    try:
                        corners = np.array([p.split(',') for p in parts], dtype=np.float32)
                        return corners
                    except:
                        return None
    return None

def calculate_iou(quad1: np.ndarray, quad2: np.ndarray) -> float:
    """
    Calcula a Interseção sobre União (IoU) de dois quadriláteros.
    """
    try:
        poly1 = Polygon(quad1)
        poly2 = Polygon(quad2)
        
        intersection_area = poly1.intersection(poly2).area
        union_area = poly1.union(poly2).area
        
        if union_area == 0:
            return 0.0
            
        return intersection_area / union_area
    except Exception:
        return 0.0

def run_crop_evaluation(dataset_path: str, iou_threshold: float = 0.5):
    """
    Executa a avaliação da etapa de recorte em um dataset.
    """
    print(f"--- Iniciando Avaliação de Recorte (Crop) ---")
    print(f"Pasta do dataset: {dataset_path}")
    print(f"Limiar de IoU para acerto: {iou_threshold}\n")

    dataset_dir = Path(dataset_path)
    image_files = list(dataset_dir.glob('*.jpg')) + \
                  list(dataset_dir.glob('*.jpeg')) + \
                  list(dataset_dir.glob('*.png'))

    if not image_files:
        print(f"ERRO: Nenhuma imagem encontrada na pasta '{dataset_path}'.")
        return

    total_images = len(image_files)
    successful_crops = 0
    failed_detections = 0 # Onde o pipeline não achou nenhuma placa
    localization_failures = [] # Onde o IoU foi muito baixo
    
    start_time = time.time()

    for i, img_path in enumerate(image_files):
        progress = (i + 1) / total_images
        print(f"\rProcessando: [{int(progress * 100):>3}%] {i+1}/{total_images} - {img_path.name}", end="")
        
        # 1. Pega o gabarito
        txt_path = img_path.with_suffix('.txt')
        gt_quad = parse_ground_truth_quad(txt_path)
        
        if gt_quad is None:
            continue

        try:
            # 2. Executa a pipeline de DETECÇÃO
            img_bgr = cv2.imread(str(img_path))
            preproc = Preprocessamento.executar(img_bgr)
            edges = Bordas.executar(preproc)
            contours = Contornos.executar(edges)
            candidatos = FiltrarContornos.executar(contours, img_bgr)

            if not candidatos:
                failed_detections += 1
                continue

            # 3. Pega o recorte previsto
            predicted_quad = candidatos[0].get("quad")
            if predicted_quad is None:
                failed_detections += 1
                continue

            # 4. Compara com o gabarito usando IoU
            iou = calculate_iou(predicted_quad, gt_quad)
            
            if iou >= iou_threshold:
                successful_crops += 1
            else:
                localization_failures.append({
                    "arquivo": img_path.name,
                    "iou_score": iou
                })

        except Exception as e:
            failed_detections += 1
            print(f"\n[AVISO] Erro crítico ao processar {img_path.name}: {e}")
            
    end_time = time.time()
    total_time = end_time - start_time

    # --- 5. Exibe o Relatório Final ---
    print("\n\n--- Relatório de Avaliação da Detecção/Recorte ---")
    print(f"Tempo total: {total_time:.2f} segundos")
    print(f"Total de imagens: {total_images}")
    print("-" * 50)
    
    accuracy = (successful_crops / total_images) * 100
    detection_failure_rate = (failed_detections / total_images) * 100
    localization_failure_rate = (len(localization_failures) / total_images) * 100

    print(f"Recortes Corretos (IoU >= {iou_threshold}): {successful_crops} ({accuracy:.2f}%)")
    print(f"Falhas de Detecção (não achou placa): {failed_detections} ({detection_failure_rate:.2f}%)")
    print(f"Falhas de Localização (achou no lugar errado): {len(localization_failures)} ({localization_failure_rate:.2f}%)")
    
    report_path = Path("relatorio_erros_recorte.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("--- Relatório Detalhado de Falhas de Localização ---\n\n")
        if not localization_failures:
            f.write("Nenhuma falha de localização encontrada.\n")
        else:
            f.write(f"{'Arquivo':<25} | {'Score IoU'}\n")
            f.write("-" * 40 + "\n")
            for fail in sorted(localization_failures, key=lambda x: x["iou_score"]):
                f.write(f"{fail['arquivo']:<25} | {fail['iou_score']:.3f}\n")

    print(f"\n[INFO] Um relatório detalhado com as falhas de localização foi salvo em: '{report_path}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script para avaliar a precisão da etapa de recorte de placa.")
    parser.add_argument("dataset_path", help="Caminho para a pasta contendo as imagens e os arquivos .txt do dataset.")
    args = parser.parse_args()
    
    run_crop_evaluation(args.dataset_path)