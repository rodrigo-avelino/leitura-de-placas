from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from datetime import datetime
from src.config.db import Base

# class TabelaAcesso(Base):
#     __tablename__ = "acessos"

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     plate_text = Column(String(16), index=True, nullable=True)
#     confidence = Column(Float, default=0.0)
#     source_path = Column(String(512))
#     plate_crop_path = Column(String(512))
#     annotated_path = Column(String(512))
#     created_at = Column(DateTime, default=datetime.utcnow)

class TabelaAcesso(Base):
    __tablename__ = "acessos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plate_text = Column(String(16), index=True, nullable=True)
    confidence = Column(Float, default=0.0)

    # imagens salvas como binário
    source_image = Column(LargeBinary)
    plate_crop_image = Column(LargeBinary)
    annotated_image = Column(LargeBinary)

    created_at = Column(DateTime, default=datetime.utcnow)