from fastapi import APIRouter

router = APIRouter()

class HealthRoute:

    @router.get("/")
    def health_check():
        return {
            "status": "ok", 
            "mensagem": "API ALPR saudável"
        }
