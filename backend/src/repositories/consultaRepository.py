from datetime import datetime
from sqlalchemy.orm import Session
from ..config.db import SessionLocal
from ..models.acessoModel import TabelaAcesso

class ConsultaRepository:
    @staticmethod
    def consultar(placa: str = None, data_inicio: datetime = None, data_fim: datetime = None):
        """
        Consulta os registros de placas no banco, com filtros opcionais.
        Retorna lista de dicionários formatados para o frontend.
        """
        db: Session = SessionLocal()
        try:
            query = db.query(TabelaAcesso)

            if placa:
                query = query.filter(TabelaAcesso.plate_text.ilike(f"%{placa}%"))

            if data_inicio:
                query = query.filter(TabelaAcesso.created_at >= data_inicio)

            if data_fim:
                query = query.filter(TabelaAcesso.created_at <= data_fim)

            registros = query.order_by(TabelaAcesso.created_at.desc()).all()

            resultado = []
            for r in registros:
                data = r.created_at.strftime("%d/%m/%Y")
                hora = r.created_at.strftime("%H:%M:%S")

                resultado.append({
                    "id": r.id,
                    "placa": r.plate_text,
                    "score": r.confidence,
                    "data": data,
                    "hora": hora,
                    "caminho_origem": r.source_path,
                    "caminho_crop": r.plate_crop_path,
                    "caminho_annotated": r.annotated_path,
                })

            return resultado

        except Exception as e:
            print(f"[ERRO] Erro ao consultar registros: {e}")
            return []

        finally:
            db.close()
