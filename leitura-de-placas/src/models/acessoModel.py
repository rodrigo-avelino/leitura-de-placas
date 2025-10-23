from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from datetime import datetime
from src.config.db import Base

# ------------------------------------------------------------------------------
# Modelo ORM da tabela "acessos".
# Representa um registro de leitura de placa: texto reconhecido, confiança,
# imagens associadas (fonte, recorte da placa e imagem anotada) e timestamp.
# Este modelo é usado pelo SQLAlchemy para mapear a tabela no SQLite (ou outro
# SGBD) e permitir CRUD via sessão (SessionLocal).
# ------------------------------------------------------------------------------

class TabelaAcesso(Base):
    __tablename__ = "acessos"  # nome físico da tabela no banco

    # Chave primária autoincremento.
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Texto da placa reconhecida. Indexada para acelerar buscas por placa.
    # Tamanho 16 é mais do que suficiente para padrões BR (7 chars), mas
    # mantemos folga para testes/expansões.
    plate_text = Column(String(16), index=True, nullable=True)

    # Confiança/score do reconhecimento (0.0–1.0 ou outra escala definida
    # pelo pipeline). No MVP usamos valor fixo 1.0 no salvamento.
    confidence = Column(Float, default=0.0)

    # Imagens armazenadas como binário (BLOB):
    # - source_image: frame/imagem original de onde a placa foi lida.
    # - plate_crop_image: recorte da região da placa (útil para visualização).
    # - annotated_image: imagem com bounding box/quadrilátero desenhado.
    # Observação: optar por BLOB simplifica distribuição (sem gerenciar paths),
    # mas aumenta o tamanho do banco. Em produção, pode-se trocar por armazenamento
    # em disco/objeto (S3 etc.) e salvar apenas paths/URLs.
    source_image = Column(LargeBinary)
    plate_crop_image = Column(LargeBinary)
    annotated_image = Column(LargeBinary)

    # Momento em que o registro foi criado. Usamos UTC por padrão para
    # evitar ambiguidade de fuso horário; a UI pode converter para o fuso local.
    created_at = Column(DateTime, default=datetime.utcnow)
