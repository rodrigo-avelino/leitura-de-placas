# Leitura Automática de Placas (ALPR)

**Objetivo:** identificar e registrar automaticamente placas de veículos a partir de imagens, para controle de entradas/saídas em estacionamentos comunitários.  
**Equipe:** Victor Kainã, Rodrigo Avelino, João Vitor e Guilherme Paiva.  
**Repo:** https://github.com/Kainan7/leitura-automatica-placas

---

## ✨ Funcionalidades
- Detecção **heurística** via contornos (didático) + *inner crop* para reduzir ruído (parafusos/aro).
- OCR com **EasyOCR** (pt/en/es), correções O↔0, I↔1, S↔5, B↔8, Z↔2 e **fallback**.
- Padrões validados:
  - BR antigo `AAA9999`, BR Mercosul `AAA9A99`
  - 2L-4D `CC5220` (diplomática/serviço), 3L-3D `ABC123` (LATAM), AR Mercosul `AA000AA`
- Persistência em **SQLite** (placa, confiança, caminhos de imagens, data/hora).
- **CLI** para lote, **Notebook PDI** (grayscale, histograma, equalização e CLAHE) e **UI Web (Streamlit)** com upload + consulta.

---

## 🧱 Estrutura
```text
.
├── src/
│ ├── app_cli.py # CLI (processa uma imagem ou pasta)
│ ├── config.py # .env, pastas e paths
│ ├── db.py # SQLAlchemy + modelo AccessRecord
│ ├── detect.py # detecção por contornos (baseline)
│ ├── ocr.py # EasyOCR + validação + correções + fallback
│ └── pipeline.py # orquestra: detecta → OCR → salva → grava no banco
├── scripts/
│ └── init_db.py # cria as tabelas
├── app_streamlit.py # interface web
├── PDI_ALPR_Exploracao.ipynb # notebook de PDI (pode estar em src/)
├── requirements.txt
├── .env.example
├── .gitignore
└── data/ # (gitignored)
├── images/ # imagens de entrada
└── output/ # saídas (recortes/anotações)

yaml
```

> Dica: execute sempre a partir da **raiz** do projeto.

---

## 💻 Requisitos
- Python **3.10+**
- Git
- Windows (testado com **Git Bash** e **PowerShell**)

---

## 🚀 Instalação

### Git Bash (recomendado)
```bash
git clone https://github.com/Kainan7/leitura-automatica-placas.git
cd leitura-automatica-placas

python -m venv .venv
source .venv/Scripts/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

PowerShell
git clone https://github.com/Kainan7/leitura-automatica-placas.git
cd leitura-automatica-placas

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

⚙️ Configuração (.env) e banco
Crie um .env (ou copie de .env.example):

ini
DB_URL=sqlite:///data/acessos.sqlite3
IMAGE_DIR=data/images
OUTPUT_DIR=data/output
Inicialize o banco:

python scripts/init_db.py

🧪 Teste rápido (CLI)
Coloque imagens em data/images/ e rode:
python -m src.app_cli --input data/images
# PNG:
# python -m src.app_cli --input data/images --pattern "*.png"
Saídas em data/output/ e registros no data/acessos.sqlite3.

📓 Notebook PDI
Registrar a venv como kernel:

python -m pip install ipykernel
python -m ipykernel install --user --name alpr-venv --display-name "Python (alpr-venv)"

Abrir:

jupyter notebook
Abrir PDI_ALPR_Exploracao.ipynb (ou src/pdi_alpr_exploracao.ipynb), selecionar o kernel Python (alpr-venv) e executar.
Mostra: dimensões, grayscale + min/max, histogramas, equalização e CLAHE, detecção/crop e OCR.

🌐 Aplicação Web (Streamlit)
pip install streamlit
streamlit run app_streamlit.py
Abas

📷 Processar imagem
Upload → expander “Análise PDI (modo notebook)” (grayscale/histogramas/equalização/CLAHE/detecção/crop/candidatos) → Processar (salva por hash, roda pipeline e grava no banco).

🔎 Consultar registros
Filtro por trecho de placa e intervalo de datas.
Agrupar por placa (mostra só o mais recente por placa).
Evitamos duplicados: upload salvo por hash e janela de idempotência por (fonte+placa) na pipeline.

🧰 Comandos úteis
Ativar venv:

Git Bash: source .venv/Scripts/activate

PowerShell: .\\.venv\\Scripts\\Activate.ps1

Ver últimos registros:

python - << 'PY'
from src.db import SessionLocal, AccessRecord
s=SessionLocal()
print([(r.id,r.plate_text,round(r.confidence or 0,2),r.created_at) for r in s.query(AccessRecord).order_by(AccessRecord.id.desc()).limit(10)])
s.close()
PY

Limpar saídas:
rm -f data/output/*     # Git Bash
# del data\output\* -Force  (PowerShell)

🛠️ Solução de problemas
ModuleNotFoundError: dotenv → ative a venv e pip install -r requirements.txt.

attempted relative import → execute na raiz e garanta src/__init__.py.

Kernel errado no Jupyter → selecione Python (alpr-venv).

Avisos do EasyOCR sobre GPU → normal se estiver em CPU.

🗺️ Roadmap
Detector YOLOv8 específico para placas.

API REST (Flask/FastAPI).

Exportar CSV/Excel de acessos.

Dockerfile/Compose.

📄 Licença
MIT (adicione LICENSE se desejar).

### Técnicas utilizadas (MVP)

**Pré-processamento (PDI)**
- Conversão para tons de cinza (BGR → Gray)
- Equalização de histograma e **CLAHE** (na análise PDI)
- **Inner-crop** (~8% das bordas) no recorte da placa para reduzir ruído (moldura/parafusos)

**Detecção de placa (baseline)**
- **Bordas/contornos** + heurísticas geométricas (razão de aspecto, área) para estimar a **bbox**

**OCR e pós-processamento**
- **EasyOCR** (pt/en/es)
- Normalização/limpeza + correções de ambiguidade: **O↔0, I↔1, S↔5, B↔8, Z↔2**
- **Validação por regex** dos formatos: `AAA9999`, `AAA9A99`, `CC5220`, `ABC123`, `AA000AA`

**Persistência e idempotência**
- **SQLite + SQLAlchemy**
- Upload salvo por **hash**; janela curta evita duplicatas por *(fonte+placa)*

### Fluxo de processamento

1. **Entrada**: caminho da imagem  
2. **Carregar** (OpenCV)  
3. **Detecção** por contornos → **bbox**  
4. **Recorte** da placa + **inner-crop**  
5. **OCR (EasyOCR)** no recorte  
6. **Pós-processamento**: normaliza, corrige, **valida por regex**, escolhe melhor candidato  
7. **Anotação**: desenha bbox/texto na original  
8. **Salvar saídas** (recorte/anotada) e **gravar no SQLite** (com proteção de duplicidade)  
9. **Retorno**: `id`, `plate_text`, `confidence`, `crop_path`, `annotated_path`, `candidates`
