from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from datetime import datetime
from ..config.db import Base

# class TabelaAcesso(Base):
#     __tablename__ = "acessos"

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     plate_text = Column(String(16), index=True, nullable=True)
#     confidence = Column(Float, default=0.0)
#     source_path = Column(String(512))
#     plate_crop_path = Column(String(512))
#     annotated_path = Column(String(512))
#     created_at = Column(DateTime, default=datetime.utcnow)

from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from datetime import datetime
from ..config.db import Base

class TabelaAcesso(Base):
    __tablename__ = "acessos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plate_text = Column(String(16), index=True, nullable=True)
    confidence = Column(Float, default=0.0)

    # Caminhos físicos (para servir via /static)
    source_path = Column(String(512))
    plate_crop_path = Column(String(512))
    annotated_path = Column(String(512))

    # Imagens em binário (backup)
    source_image = Column(LargeBinary)
    plate_crop_image = Column(LargeBinary)
    annotated_image = Column(LargeBinary)

    created_at = Column(DateTime, default=datetime.utcnow)
