import uvicorn
from fastapi import FastAPI, WebSocket, File, UploadFile, Depends, Query, WebSocketDisconnect, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from datetime import datetime, date
from typing import List, Optional
import pydantic
import numpy as np
import cv2
import base64
import io
import sys
import asyncio

# Importa o seu controller e serviços
from src.controllers.placaController import PlacaController
from src.config.db import criarTabela

# --- Modelos Pydantic (Tipagem da API) ---
class RegistroResponse(pydantic.BaseModel):
    placa: Optional[str] = None
    tipo_placa: Optional[str] = None
    data: str
    imagem: Optional[str] = None # Imagem Base64

class HealthCheck(pydantic.BaseModel):
    status: str

# --- Função Auxiliar de Codificação ---
def _encode_image_to_base64(image_array: np.ndarray) -> str:
    if image_array is None or image_array.size == 0:
        return None
    try:
        if len(image_array.shape) == 2:
            image_array = cv2.cvtColor(image_array, cv2.COLOR_GRAY2BGR)
        image_rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        success, buffer = cv2.imencode(".png", image_rgb)
        if not success:
            return None
        img_base64 = base64.b64encode(buffer).decode("utf-8")
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        print(f"Erro ao codificar imagem: {e}", file=sys.stderr)
        return None

# --- Inicialização do App FastAPI ---
app = FastAPI(
    title="API de ALPR",
    description="Processa e consulta placas de veículos.",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.on_event("startup")
def on_startup():
    print("Iniciando API e verificando banco de dados...")
    criarTabela()
    print("Banco de dados pronto.")

# --- Endpoints GET e Consulta ---
@app.get("/", response_model=HealthCheck)
def read_root():
    return {"status": "API de ALPR online"}

@app.get("/api/v1/registros", response_model=List[RegistroResponse])
async def consultar_registros(
    placa: Optional[str] = Query(None, description="Filtrar por texto contido na placa"),
    data_inicio: Optional[date] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    data_fim: Optional[date] = Query(None, description="Data final (YYYY-MM-DD)")
):
    dt_inicio = datetime.combine(data_inicio, datetime.min.time()) if data_inicio else None
    dt_fim = datetime.combine(data_fim, datetime.max.time()) if data_fim else None
    filtros = { "placa": placa, "data_inicio": dt_inicio, "data_fim": dt_fim }
    registros = await run_in_threadpool(PlacaController.consultarRegistros, arg=filtros)
    return registros

# --- NOVO ENDPOINT DE EXCLUSÃO (DELETE) ---
@app.delete("/api/v1/registros/{registro_id}", status_code=204) # 204 No Content
async def deletar_registro(registro_id: int):
    """
    Exclui um registro de placa pelo seu ID.
    """
    # Executa a função de exclusão no controller em um thread pool
    sucesso = await run_in_threadpool(PlacaController.deletarRegistro, id=registro_id)
    
    if not sucesso:
        # Se o PlacaController retornar False, o registro não foi encontrado
        raise HTTPException(status_code=404, detail=f"Registro ID {registro_id} não encontrado.")
    
    # Retorna status 204 (No Content), que significa sucesso na exclusão
    return Response(status_code=204)


# --- ENDPOINT WEBSOCKET ---
@app.websocket("/ws/processar-imagem")
async def processar_imagem_ws(websocket: WebSocket):
    await websocket.accept() 
    
    main_event_loop = asyncio.get_running_loop()

    try:
        image_bytes = await websocket.receive_bytes() 
        
        data_capturada = datetime.utcnow()
        await websocket.send_json({"step": "start", "message": "Imagem recebida, iniciando processamento..."})

        async def send_update_to_client(delta: dict):
            encoded_delta = delta.copy()
            if delta.get("step") == "candidates_found" and "data" in delta:
                encoded_candidates = []
                for cand in delta["data"]:
                    cand_copy = cand.copy()
                    cand_copy["imagem"] = _encode_image_to_base64(cand_copy.get("imagem"))
                    encoded_candidates.append(cand_copy)
                encoded_delta["data"] = encoded_candidates
            elif "image" in delta:
                encoded_delta["image"] = _encode_image_to_base64(delta["image"])
            await websocket.send_json(encoded_delta)

        def on_update_sync_callback(delta: dict):
            asyncio.run_coroutine_threadsafe(
                send_update_to_client(delta),
                main_event_loop
            )

        final_result = await run_in_threadpool(
            PlacaController.processarImagem,
            source_image=io.BytesIO(image_bytes),
            data_capturada=data_capturada,
            on_update=on_update_sync_callback
        )
        
        await websocket.send_json({
            "step": "final_result", 
            "status": final_result.get("status"),
            "texto_final": final_result.get("texto_final"),
            "padrao_placa": final_result.get("padrao_placa")
        })

        await websocket.close()

    except WebSocketDisconnect:
        print("Cliente WebSocket desconectado.")
    except Exception as e:
        print(f"Erro no WebSocket: {e}", file=sys.stderr)
        try:
            await websocket.send_json({"step": "error", "message": f"Erro interno no servidor: {e}"})
            await websocket.close()
        except:
            pass