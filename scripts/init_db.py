"""
Script d'initialisation de la base de données.
Crée les tables et index si inexistants.
À lancer une seule fois, ou de manière idempotente.
"""
import psycopg2
import sys
from pathlib import Path

# Permet l'import depuis la racine
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.config import settings, logger

DDL = """
CREATE TABLE IF NOT EXISTS raw_jobs (
    id              SERIAL PRIMARY KEY,
    source          TEXT NOT NULL,
    raw_data        JSONB NOT NULL,
    collected_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    hash            TEXT NOT NULL UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_raw_jobs_source
    ON raw_jobs(source);

CREATE INDEX IF NOT EXISTS idx_raw_jobs_collected_at
    ON raw_jobs(collected_at);

CREATE INDEX IF NOT EXISTS idx_raw_jobs_raw_data
    ON raw_jobs USING GIN(raw_data);
"""


def init_db() -> None:
    """Initialise le schéma Bronze de la base de données."""
    logger.info("Initialisation de la base de données...")
    try:
        with psycopg2.connect(
            host="localhost",
            port=settings.postgres_port,
            dbname=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(DDL)
            conn.commit()
        logger.info("Base de données initialisée ✅")
    except Exception as e:
        logger.error(f"Erreur initialisation BDD : {e}")
        raise


if __name__ == "__main__":
    init_db()
