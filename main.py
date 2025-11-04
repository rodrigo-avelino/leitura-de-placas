import uvicorn
from fastapi import FastAPI, WebSocket, File, UploadFile, Depends, Query, WebSocketDisconnect
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

# --- Função Auxiliar de Codificação (Sem alterações) ---
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

# --- Inicialização do App FastAPI (Sem alterações) ---
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

# --- Endpoints da API (Sem alterações) ---
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

# --- ENDPOINT WEBSOCKET (CORRIGIDO) ---
@app.websocket("/ws/processar-imagem")
async def processar_imagem_ws(websocket: WebSocket):
    # 1. CORREÇÃO: Remove 'max_size' de accept()
    await websocket.accept() 
    
    main_event_loop = asyncio.get_running_loop()

    try:
        # 2. CORREÇÃO: Remove 'max_size' de receive_bytes()
        # O limite padrão de 1MB é suficiente para o upload da imagem
        image_bytes = await websocket.receive_bytes() 
        
        data_capturada = datetime.utcnow()
        await websocket.send_json({"step": "start", "message": "Imagem recebida, iniciando processamento..."})

        # (Função interna 'send_update_to_client' - Sem alterações)
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

        # (Função interna 'on_update_sync_callback' - Sem alterações)
        def on_update_sync_callback(delta: dict):
            asyncio.run_coroutine_threadsafe(
                send_update_to_client(delta),
                main_event_loop
            )

        # (Execução do pipeline - Sem alterações)
        final_result = await run_in_threadpool(
            PlacaController.processarImagem,
            source_image=io.BytesIO(image_bytes),
            data_capturada=data_capturada,
            on_update=on_update_sync_callback
        )
        
        # (Envio do resultado final - Sem alterações)
        await websocket.send_json({
            "step": "final_result", 
            "status": final_result.get("status"),
            "texto_final": final_result.get("texto_final"),
            "padrao_placa": final_result.get("padrao_placa")
        })

        # (Correção da race condition - Sem alterações)
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
    # finally:
        # (bloco 'finally' removido)