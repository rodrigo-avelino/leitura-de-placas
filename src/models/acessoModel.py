from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from datetime import datetime
from src.config.db import Base

class TabelaAcesso(Base):
    __tablename__ = "acessos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plate_text = Column(String(16), index=True, nullable=True)
    confidence = Column(Float, default=0.0)
    plate_type = Column(String(20), nullable=True, index=True) 
    source_image = Column(LargeBinary)
    plate_crop_image = Column(LargeBinary)
    annotated_image = Column(LargeBinary)
    created_at = Column(DateTime, default=datetime.now)  # Alterado de utcnow para now (horário local)