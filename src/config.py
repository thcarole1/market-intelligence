import logging
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Racine du projet
ROOT = Path(__file__).resolve().parent.parent


def setup_logging() -> logging.Logger:
    """
    Configure le logging standard pour tout le projet.
    Format uniforme, niveau INFO par défaut.
    """
    log_dir = ROOT / "logs"
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            # Console
            logging.StreamHandler(),
            # Fichier
            logging.FileHandler(log_dir / "pipeline.log", encoding="utf-8")
        ]
    )
    return logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_port: int = 5432

    # pgAdmin
    pgadmin_email: str
    pgadmin_password: str
    pgadmin_port: int = 5050

    # France Travail
    francetravail_client_id: str
    francetravail_client_secret: str


# Instances uniques importées partout dans le projet
settings = Settings()
logger = setup_logging()
