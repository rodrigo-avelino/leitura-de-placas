from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from src.config.db import Base

class TabelaAcesso(Base):
    __tablename__ = "acessos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plate_text = Column(String(16), index=True, nullable=True)
    confidence = Column(Float, default=0.0)

    # caminhos dos arquivos em disco
    source_path = Column(String(512))
    plate_crop_path = Column(String(512))
    annotated_path = Column(String(512))

    created_at = Column(DateTime, default=datetime.utcnow)

#VALIDAR O MVP:

#alinha model ↔ persistência ↔ consulta: a UI passa a exibir os registros corretamente a partir dos paths.

#não toca na lógica de detecção/OCR/validação — apenas no esquema de armazenamento.