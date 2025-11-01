from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.routes import placaRoute, saudeRoute

app = FastAPI(title="ALPR API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(placaRoute.router, prefix="/placas", tags=["Reconhecimento"])
app.include_router(saudeRoute.router, prefix="/saude", tags=["Status"])

app.mount("/static", StaticFiles(directory="src/static"), name="static")

@app.get("/")
def home():
    print("API ALPR está ativa!")
    return {"mensagem": "API ALPR está ativa!"}

#lanca um uvicorn src.api:app --reload para inicializar a api 