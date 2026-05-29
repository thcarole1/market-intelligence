import logging
import requests
from src.config import settings
from src.ingestion.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class RemotiveCollector(BaseCollector):
    """
    Collecteur pour l'API publique Remotive.
    Pas d'authentification requise.
    Documentation : https://remotive.com/api
    """

    API_URL = "https://remotive.com/api/remote-jobs"
    CATEGORIES = ["software-dev", "data", "devops-sysadmin"]

    def __init__(self) -> None:
        super().__init__(source_name="remotive")

    def _fetch_jobs(self, category: str) -> list[dict]:
        """Récupère toutes les offres d'une catégorie."""
        response = requests.get(
            self.API_URL,
            params={"category": category},
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("jobs", [])

    def collect(self) -> int:
        """
        Collecte les offres des catégories data et tech.
        Retourne le nombre d'offres insérées.
        """
        logger.info("[remotive] Démarrage collecte...")
        inserted = 0

        try:
            for category in self.CATEGORIES:
                logger.info(f"[remotive] Catégorie : '{category}'")
                jobs = self._fetch_jobs(category)
                logger.info(f"[remotive] {len(jobs)} offres récupérées")

                for job in jobs:
                    if self._save_raw(job):
                        inserted += 1

        except requests.HTTPError as e:
            logger.error(f"[remotive] Erreur API : {e}")
        except Exception as e:
            logger.error(f"[remotive] Erreur inattendue : {e}")
        finally:
            self.close()

        logger.info(f"[remotive] Collecte terminée : {inserted} offres insérées.")
        return inserted


if __name__ == "__main__":
    collector = RemotiveCollector()
    collector.collect()
