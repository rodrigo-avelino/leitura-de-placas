from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = Path(__file__).resolve().parent.parent

#vai salvar em config/banco/
BANCO_DIR = BASE_DIR / 'config' / 'banco'
BANCO_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = BANCO_DIR / 'placas.db'
DB_URL = f"sqlite:///{DB_PATH}"

UPLOAD_DIR = BASE_DIR / 'static' / 'uploads'
CROP_DIR = BASE_DIR / 'static' / 'crops'
ANNOTATED_DIR = BASE_DIR / 'static' / 'annotated'

for directory in [UPLOAD_DIR, CROP_DIR, ANNOTATED_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

#config padrao do alchemy
engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

#cria a tabela
def criarTabela():
    #importe ta dentro da funcao para evitar erro circular
    from models.acessoModel import TabelaAcesso
    Base.metadata.create_all(bind=engine)
