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

-- Table des skills extraits par NLP
CREATE TABLE IF NOT EXISTS job_skills (
    id              SERIAL PRIMARY KEY,
    raw_job_id      INTEGER NOT NULL REFERENCES raw_jobs(id) ON DELETE CASCADE,
    skill           TEXT NOT NULL,
    skill_type      TEXT NOT NULL CHECK (skill_type IN ('hard', 'soft')),
    extracted_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_job_skills_raw_job_id
    ON job_skills(raw_job_id);

CREATE INDEX IF NOT EXISTS idx_job_skills_skill
    ON job_skills(skill);

CREATE UNIQUE INDEX IF NOT EXISTS idx_job_skills_unique
    ON job_skills(raw_job_id, skill);

-- Table de monitoring du pipeline
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id              SERIAL PRIMARY KEY,
    run_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    status          TEXT NOT NULL CHECK (status IN ('success', 'failure', 'partial')),
    duration_seconds FLOAT,
    details         JSONB
);

-- Table de métriques par source
CREATE TABLE IF NOT EXISTS source_metrics (
    id              SERIAL PRIMARY KEY,
    run_id          INTEGER REFERENCES pipeline_runs(id),
    source          TEXT NOT NULL,
    nb_collected    INTEGER DEFAULT 0,
    nb_inserted     INTEGER DEFAULT 0,
    nb_duplicates   INTEGER DEFAULT 0,
    status          TEXT NOT NULL CHECK (status IN ('success', 'failure', 'skipped')),
    error_message   TEXT,
    measured_at     TIMESTAMP NOT NULL DEFAULT NOW()
);
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
