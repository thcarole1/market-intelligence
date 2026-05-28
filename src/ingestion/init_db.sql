-- Couche Bronze : stockage des offres brutes
-- Le champ raw_data contient le JSON complet de chaque source

CREATE TABLE IF NOT EXISTS raw_jobs (
    id              SERIAL PRIMARY KEY,
    source          TEXT NOT NULL,
    raw_data        JSONB NOT NULL,
    collected_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    hash            TEXT NOT NULL UNIQUE
);

-- Index sur la source pour filtrer rapidement par origine
CREATE INDEX IF NOT EXISTS idx_raw_jobs_source
    ON raw_jobs(source);

-- Index sur la date de collecte pour les requêtes temporelles
CREATE INDEX IF NOT EXISTS idx_raw_jobs_collected_at
    ON raw_jobs(collected_at);

-- Index GIN sur raw_data pour rechercher dans le JSON
CREATE INDEX IF NOT EXISTS idx_raw_jobs_raw_data
    ON raw_jobs USING GIN(raw_data);
