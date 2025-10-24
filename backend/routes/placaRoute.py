from fastapi import APIRouter, UploadFile, File
from datetime import datetime
from pathlib import Path
import shutil
from backend.controllers.placaController import PlacaController

router = APIRouter()

#deve apontar para a pasta backend (mesmo que o controller)
BASE_DIR = Path(__file__).resolve().parent.parent  # agora aponta para 'backend'
UPLOAD_DIR = BASE_DIR / "static" / "uploads"

# Garantir que o diretório existe
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

#Recebe uma imagem (JPG/PNG), salva em 'static/uploads' e processa a placa via PlacaController.
@router.post("/processar")
async def processar_placa(imagem: UploadFile = File(...)):
    try:
        nome_arquivo = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{imagem.filename}"
        destino = UPLOAD_DIR / nome_arquivo

        with open(destino, "wb") as buffer:
            shutil.copyfileobj(imagem.file, buffer)

        resultado = PlacaController.processarImagem(nome_arquivo)
        return resultado

    except Exception as e:
        return {
            "status": "erro", 
            "mensagem": str(e)
        }

#Consulta os registros de placas processadas (persistidas no banco).
@router.get("/consultar")
def consultar_registros(placa: str = None, data_inicio: str = None, data_fim: str = None):
    try:
        di = datetime.fromisoformat(data_inicio) if data_inicio else None
        df = datetime.fromisoformat(data_fim) if data_fim else None
        registros = PlacaController.consultarRegistros(placa=placa, data_inicio=di, data_fim=df)
        return {
            "status": "ok", 
            "dados": registros
        }
    except Exception as e:
        return {
            "status": "erro", 
            "mensagem": str(e)
        }
