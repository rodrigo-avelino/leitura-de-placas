import shutil
from fastapi import APIRouter, UploadFile, File
from datetime import datetime
from pathlib import Path

from ..controllers.placaController import PlacaController
from ..repositories.consultaRepository import ConsultaRepository

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class PlacaRoute:

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
            return {"status": "erro", "mensagem": str(e)}

    @router.get("/consultar")
    def consultar_registros(placa: str = None, data_inicio: str = None, data_fim: str = None):
        try:
            di = datetime.fromisoformat(data_inicio) if data_inicio else None
            df = datetime.fromisoformat(data_fim) if data_fim else None

            registros = ConsultaRepository.consultar(placa, di, df)
            base_url = "http://localhost:8000"  # futuramente pode vir de .env

            # Adiciona URLs completas das imagens
            for r in registros:
                if r.get("caminho_crop"):
                    r["url_crop"] = f"{base_url}/{r['caminho_crop'].replace('\\', '/')}"
                if r.get("caminho_origem"):
                    r["url_origem"] = f"{base_url}/{r['caminho_origem'].replace('\\', '/')}"
                if r.get("caminho_annotated"):
                    r["url_annotated"] = f"{base_url}/{r['caminho_annotated'].replace('\\', '/')}"

            return {"status": "ok", "dados": registros}

        except Exception as e:
            return {"status": "erro", "mensagem": str(e)}
