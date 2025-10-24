# Relatório Comparativo de Motores OCR para ALPR

**Data:** 23 de Outubro de 2025
**Dataset:** fotos_dataset_juntas (10.000 imagens)
**Script de Avaliação:** `evaluate_full_pipeline.py` (v3.x com fallback e métricas)
**Parâmetro de Detecção:** IoU Threshold >= 0.1
**Parâmetro de Desambiguação (PaddleOCR):** Blue Threshold = 0.12

---

## Métricas Avaliadas

### 1. Métricas de Desempenho (Velocidade)

* **1.1. Latência Média por Imagem (segundos/imagem):**
    * *O que mede:* Tempo médio para processar uma única imagem.
    * *Como medir:* Tempo Total de Processamento / Número Total de Imagens.
    * *Unidade:* Segundos por imagem.
* **1.2. Frames Por Segundo (FPS):**
    * *O que mede:* Número de imagens processadas por segundo (throughput).
    * *Como medir:* Número Total de Imagens / Tempo Total de Processamento.
    * *Unidade:* Frames por segundo (FPS).

### 2. Métricas de Precisão (Qualidade)

* **2.1. Acurácia End-to-End (%):**
    * *O que mede:* Percentual de imagens com leitura 100% correta (detecção + OCR + validação). A métrica principal de sucesso.
    * *Como medir:* Comparar resultado final com gabarito.
    * *Métrica:* `(Total Leituras Corretas / Total Processadas) * 100`.
* **2.2. Acurácia da Detecção (%):**
    * *O que mede:* Precisão da localização da placa (IoU >= 0.1). Isola erros de detecção.
    * *Como medir:* Comparar IoU do recorte previsto com gabarito.
    * *Métrica:* `(Total Detecções Corretas / Total Processadas) * 100`.
* **2.3. Taxa de Erro por Caractere (CER) (%):**
    * *O que mede:* Percentual de caracteres individuais lidos incorretamente (avaliação granular do OCR).
    * *Como medir:* Distância de Levenshtein entre leitura e gabarito, somada para todo o dataset.
    * *Métrica:* `(Total Erros Caractere / Total Caracteres Gabarito) * 100`.

---

## Resultados por Motor OCR

### 1. PaddleOCR (com fallback e `blue_threshold=0.12`)

* **Desempenho:**
    * Latência Média: **0.3775** seg/img
    * FPS: **2.65** FPS
* **Precisão:**
    * Acurácia E2E: 7206 / 10000 (**72.06%**)
    * Acurácia Detecção (IoU>=0.1): 8500 / 10000 (85.00%)
    * CER: 9726 / 65051 (**14.95%**)
* **Falhas Detalhadas:**
    * Leituras Incorretas: 1608
    * Falhas de Detecção: 707
    * Falhas OCR/Validação: 479

### 2. EasyOCR

* **Desempenho:**
    * Latência Média: **0.4577** seg/img
    * FPS: **2.18** FPS
* **Precisão:**
    * Acurácia E2E: 3099 / 10000 (**30.99%**)
    * Acurácia Detecção (IoU>=0.1): 8503 / 10000 (85.03%)
    * CER: 21437 / 65051 (**32.95%**)
* **Falhas Detalhadas:**
    * Leituras Incorretas: 3119
    * Falhas de Detecção: 707
    * Falhas OCR/Validação: 3075

### 3. Pytesseract (Otimizado)

* **Desempenho:**
    * Latência Média: **0.7279** seg/img
    * FPS: **1.37** FPS
* **Precisão:**
    * Acurácia E2E: 2202 / 10000 (**22.02%**)
    * Acurácia Detecção (IoU>=0.1): 8502 / 10000 (85.02%)
    * CER: 32440 / 65051 (**49.87%**)
* **Falhas Detalhadas:**
    * Leituras Incorretas: 3287
    * Falhas de Detecção: 707
    * Falhas OCR/Validação: 3804

### 4. Keras-OCR

* **Desempenho:**
    * Latência Média: **0.6895** seg/img
    * FPS: **1.45** FPS
* **Precisão:**
    * Acurácia E2E: 693 / 10000 (**6.93%**)
    * Acurácia Detecção (IoU>=0.1): 8491 / 10000 (84.91%)
    * CER: 31373 / 65051 (**48.23%**)
* **Falhas Detalhadas:**
    * Leituras Incorretas: 4363
    * Falhas de Detecção: 707
    * Falhas OCR/Validação: 4237

---

## Conclusão Preliminar

Com base nos testes realizados no dataset 'fotos_dataset_juntas' (10k imagens), utilizando a mesma pipeline de detecção e o fallback inteligente:

* **PaddleOCR** apresentou o melhor desempenho geral, alcançando **72.06%** de Acurácia End-to-End e a menor Taxa de Erro por Caractere (**14.95%**). Também demonstrou ser o mais rápido em termos de Latência e FPS.
* **EasyOCR** ficou em segundo lugar, mas com uma Acurácia E2E significativamente menor (**30.99%**) e um CER mais que o dobro do PaddleOCR (**32.95%**).
* **Pytesseract**, mesmo com otimizações, obteve apenas **22.02%** de Acurácia E2E e um CER muito alto (**49.87%**), além de ser o mais lento.
* **Keras-OCR** apresentou o pior desempenho neste cenário, com apenas **6.93%** de Acurácia E2E e um CER de **48.23%**.

**Recomendação:** Manter o **PaddleOCR** como motor principal e focar em otimizar ainda mais a lógica de desambiguação ou outros hiperparâmetros para tentar reduzir as falhas restantes.