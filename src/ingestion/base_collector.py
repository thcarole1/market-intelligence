import hashlib
import json
import logging
import psycopg2
from abc import ABC, abstractmethod
from src.config import settings

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """
    Classe abstraite dont héritent tous les collecteurs.
    Définit l'interface commune et les méthodes utilitaires.
    """

    def __init__(self, source_name: str) -> None:
        self.source_name = source_name
        self.conn = self._connect_db()
        logger.info(f"[{self.source_name}] Connexion BDD établie ✅")

    def _connect_db(self) -> psycopg2.extensions.connection:
        """Connexion à PostgreSQL via pydantic-settings."""
        return psycopg2.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            dbname=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password
        )

    def _generate_hash(self, data: dict) -> str:
        """
        Génère une empreinte SHA-256 unique par offre.
        Garantit la déduplication au niveau base de données.
        """
        raw = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode()).hexdigest()

    def _save_raw(self, data: dict) -> bool:
        """
        Insère une offre brute dans raw_jobs.
        Retourne True si insertion, False si doublon.
        """
        hash_value = self._generate_hash(data)
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO raw_jobs (source, raw_data, hash)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (hash) DO NOTHING
                """, (self.source_name, json.dumps(data), hash_value))
            self.conn.commit()
            inserted = cur.rowcount > 0
            if inserted:
                logger.debug(f"[{self.source_name}] Offre insérée : {hash_value[:8]}...")
            else:
                logger.debug(f"[{self.source_name}] Doublon ignoré : {hash_value[:8]}...")
            return inserted
        except Exception as e:
            self.conn.rollback()
            logger.error(f"[{self.source_name}] Erreur insertion : {e}")
            return False

    def close(self) -> None:
        """Ferme proprement la connexion PostgreSQL."""
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info(f"[{self.source_name}] Connexion BDD fermée ✅")

    @abstractmethod
    def collect(self) -> int:
        """
        Méthode principale à implémenter dans chaque collecteur.
        Retourne le nombre d'offres insérées.
        """
        pass
