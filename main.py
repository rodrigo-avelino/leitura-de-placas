import uvicorn
from fastapi import FastAPI, WebSocket, File, UploadFile, Depends, Query, WebSocketDisconnect, HTTPException, status # << ADIÇÃO
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
from contextlib import asynccontextmanager

# Importa o seu controller e serviços
from src.controllers.placaController import PlacaController
from src.config.db import criarTabela # Importa a função de criar tabela

# --- Modelos Pydantic (Tipagem da API) ---
class RegistroResponse(pydantic.BaseModel):
    placa: Optional[str] = None
    tipo_placa: Optional[str] = None
    data: str
    imagem: Optional[str] = None # Imagem Base64
    id: Optional[int] = None

class HealthCheck(pydantic.BaseModel):
    status: str

# --- (Função Auxiliar de Codificação - Sem alterações) ---
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

# --- GERENCIADOR DE CONEXÕES WEBSOCKET PARA REGISTROS ---
class ConnectionManager:
    """Gerencia as conexões WebSocket ativas para notificações de registros."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Nova conexão de registro estabelecida. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"Conexão de registro encerrada. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Envia a mensagem (o novo registro) para todos os clientes ativos."""
        send_tasks = [connection.send_json(message) for connection in self.active_connections]
        
        done, pending = await asyncio.wait(
            send_tasks, return_when=asyncio.FIRST_EXCEPTION
        )
        
        for task in done:
            if task.exception():
                try:
                    coro = task.get_coro()
                    ws = coro.get_wrapped_object()
                    self.active_connections.remove(ws)
                    print("Conexão removida devido a falha no broadcast.")
                except Exception as e:
                    print(f"Erro ao remover conexão quebrada: {e}")

# Instância global do manager para a API
registro_manager = ConnectionManager()


# --- GERENCIADOR LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando API e verificando banco de dados...")
    criarTabela()
    print("Banco de dados pronto.")
    
    yield
    
    print("API desligada.")

# --- INICIALIZAR O APP FASTAPI COM O LIFESPAN ---
app = FastAPI(
    title="API de ALPR",
    description="Processa e consulta placas de veículos.",
    version="1.0.0",
    lifespan=lifespan
)

# Configuração do CORS (Sem alterações)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- ENDPOINTS HTTP ---
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

# --- NOVO ENDPOINT DE DELEÇÃO (DELETE) ---
@app.delete("/api/v1/registros/{registro_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_registro_http(registro_id: int):
    """
    Endpoint HTTP para deletar um registro com base no ID.
    Retorna 204 No Content em caso de sucesso.
    """
    sucesso = PlacaController.deletarRegistro(registro_id)
    
    if not sucesso:
        # Retorna 404 se o registro não foi encontrado (o que o frontend espera)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Registro com ID {registro_id} não encontrado."
        )
    # Retorna 204 automaticamente devido ao status_code no decorador
    return

# --- ENDPOINT WEBSOCKET PARA PROCESSAMENTO (ALPR) ---
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
        
        # --- LÓGICA DE WEBSOCKET DE REGISTRO (Broadcast) ---
        if final_result.get("status") == "ok":
            registro_salvo = {
                "id": final_result.get("id"),
                "placa": final_result.get("texto_final"),
                "tipo_placa": final_result.get("padrao_placa"),
                "data": final_result.get("data_registro"), 
                "imagem": final_result.get("imagem_base64"), 
            }
            asyncio.run_coroutine_threadsafe(
                 registro_manager.broadcast(registro_salvo),
                 main_event_loop
            )

        # Envia o resultado final do processamento ALPR para o cliente atual
        await websocket.send_json({
            "step": "final_result", 
            "status": final_result.get("status"),
            "texto_final": final_result.get("texto_final"),
            "padrao_placa": final_result.get("padrao_placa"),
            "id": final_result.get("id"),
            "data_registro": final_result.get("data_registro")
        })
        await websocket.close()

    except WebSocketDisconnect:
        print("Cliente WebSocket de processamento desconectado.")
    except Exception as e:
        print(f"Erro no WebSocket de processamento: {e}", file=sys.stderr)
        try:
            await websocket.send_json({"step": "error", "message": f"Erro interno no servidor: {e}"})
            await websocket.close()
        except:
            pass 


# --- NOVO ENDPOINT WEBSOCKET PARA REGISTROS EM TEMPO REAL ---
@app.websocket("/ws/registros")
async def websocket_registros_endpoint(websocket: WebSocket):
    await registro_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        registro_manager.disconnect(websocket)
    except Exception as e:
        print(f"Erro inesperado no WS de registro: {e}")
        registro_manager.disconnect(websocket)


# --- Ponto de entrada ---
if __name__ == "__main__":
    print("Iniciando servidor Uvicorn em http://127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)