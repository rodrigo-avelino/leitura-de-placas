from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from datetime import datetime
from .config import settings

Base = declarative_base()

class AccessRecord(Base):
    __tablename__ = "acessos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plate_text = Column(String(16), index=True, nullable=True)
    confidence = Column(Float, default=0.0)
    source_path = Column(String(512))
    plate_crop_path = Column(String(512))
    annotated_path = Column(String(512))
    created_at = Column(DateTime, default=datetime.utcnow)

engine = create_engine(settings.db_url, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def create_tables():
    Base.metadata.create_all(bind=engine)