# ALPR — Sistema de Leitura Automática de Placas

Este projeto implementa um **sistema de reconhecimento automático de placas veiculares (ALPR)** utilizando **Python + OpenCV + OCR + Streamlit**.  
A aplicação permite **processar imagens de veículos**, extrair e validar a placa, armazenar os resultados em banco de dados e consultar registros anteriores por meio de uma interface web.

---

## 📌 Funcionalidades

- **Upload de imagens** (JPG/PNG).  
- **Pipeline de visão computacional**:
  1. Pré-processamento da imagem (grayscale, equalização, CLAHE).  
  2. Detecção de bordas e contornos.  
  3. Filtro de candidatos a placa.  
  4. Recorte da placa.  
  5. Binarização.  
  6. Segmentação de caracteres.  
  7. OCR (placa inteira e por caracteres).  
  8. Montagem da sequência.  
  9. Validação da placa segundo padrão BR.  
- **Armazenamento no banco de dados**: placa reconhecida, confiança, data/hora, caminhos das imagens (original, recorte, anotada).  
- **Histórico de consultas**: filtro por placa e intervalo de datas, agrupamento por mais recente.  
- **Exibição das etapas de processamento** para análise didática.

---

## 🗂️ Estrutura do Projeto
src/
├── app.py # Aplicação principal Streamlit
├── components/ # Componentes de UI (upload box, etapas, filtros, etc.)
├── controllers/ # Lógica de controle (PlacaController, ConsultaController)
├── services/ # Serviços do pipeline (bordas, contornos, OCR, validação, etc.)
├── models/ # Modelos ORM (AccessRecord, TabelaAcesso)
├── pages/ # Instancia das page do Front UI
├── config/ # Configurações do banco (SQLAlchemy)
├       └── banco
├               └── placas.db (banco de dados nessa pasta)
├── static/ # Imagens geradas, utilizada pasta teste no back (uploads, crops, annotated, steps)


## ⚙️ Tecnologias Utilizadas

- **Python 3.10+**
- **Streamlit** — front-end rápido e interativo.
- **OpenCV** — processamento de imagem (pré-processamento, bordas, contornos, recorte).
- **easyOCR** — reconhecimento óptico de caracteres.
- **SQLAlchemy** — ORM para persistência no banco de dados.
- **SQLite** — banco de dados para registros de placas.

---

## ▶️ Como Rodar

1. **Clone o repositório**
   ```bash
   git clone https://github.com/seu-repo/alpr.git

2. **Ambiente virtual**
    ```bash
    python -m venv venv

3. **baixa as dependencias**
    ```bash
    pip install -r requirements.txt

4. **cria o banco**
    ```bash
    python banco.py

5. **rode a aplicacao**
    ```bash
    streamlit run app.py

## Front END

--**Processar Imagem**
--**Consulta registros**

*ainda precisa ajustar o front end*

## 📖 Fluxo do Pipeline Do Back End
    1.Upload → usuário envia imagem.
    2.Pré-processamento → equalização, contraste, CLAHE.
    3.Detecção de contornos e bordas → encontra regiões candidatas.
    4.Filtro de candidatos → descarta falsos positivos.
    5.Recorte da placa → gera imagem isolada.
    6.Binarização + Segmentação → separa caracteres.
    7.OCR → reconhecimento dos caracteres.
    8.Montagem + Validação → gera a placa final. (essa parte precisa rever melhor, talvez consiga melhor mais)
    9.Persistência → salva no banco a placa, score e imagens associadas.
    10.Consulta → recupera registros por filtros no Streamlit.

Back end ja esta finalizado, com possiveis revisoes posteriores para melhor a validacao e montagem dos caracteres para algumas situacoes mais graves