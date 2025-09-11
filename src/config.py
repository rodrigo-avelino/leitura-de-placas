from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    db_url: str = os.getenv("DB_URL", "sqlite:///data/acessos.sqlite3")
    image_dir: Path = Path(os.getenv("IMAGE_DIR", "data/images"))
    output_dir: Path = Path(os.getenv("OUTPUT_DIR", "data/output"))

settings = Settings()

# Garante que as pastas existam
settings.image_dir.mkdir(parents=True, exist_ok=True)
settings.output_dir.mkdir(parents=True, exist_ok=True)