import logging
import requests
from src.ingestion.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class GreenhouseCollector(BaseCollector):
    """
    Collecteur pour l'API publique Greenhouse.
    Cible les entreprises tech/data connues utilisant Greenhouse comme ATS.
    Aucune authentification requise.
    Documentation : https://developers.greenhouse.io/job-board.html
    """

    API_URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs"

    # Entreprises tech/data connues utilisant Greenhouse
    BOARD_TOKENS = [
        "aircall", "algolia", "alan", "back-market", "blablacar",
        "contentsquare", "dataiku", "doctolib", "drivy", "exotec",
        "gymlib", "jobteaser", "kantox", "kyriba", "ledger",
        "lydia", "mirakl", "molotov", "october", "ogury",
        "payfit", "pennylane", "phenix", "qonto", "scaleway",
        "skeepers", "slimpay", "snowflake", "spendesk", "theodo",
        "toucan-toco", "vestiairecollective", "withings", "yousign"
    ]

    # Mots-clés pour filtrer les offres pertinentes
    KEYWORDS = ["data engineer", "data engineering", "analytics engineer"]

    def __init__(self) -> None:
        super().__init__(source_name="greenhouse")

    def _fetch_jobs(self, token: str) -> list[dict]:
        """Récupère toutes les offres publiées d'une entreprise."""
        response = requests.get(
            self.API_URL.format(token=token),
            params={"content": "true"},
            timeout=30
        )

        # Certaines entreprises n'ont plus de board actif
        if response.status_code == 404:
            logger.debug(f"[greenhouse] Board introuvable : '{token}'")
            return []

        response.raise_for_status()
        return response.json().get("jobs", [])

    def _is_relevant(self, job: dict) -> bool:
        """Filtre les offres contenant les mots-clés cibles."""
        title = job.get("title", "").lower()
        return any(kw in title for kw in self.KEYWORDS)

    def collect(self) -> int:
        """
        Collecte les offres data engineer depuis tous les boards Greenhouse.
        Retourne le nombre d'offres insérées.
        """
        logger.info("[greenhouse] Démarrage collecte...")
        inserted = 0
        total_fetched = 0

        try:
            for token in self.BOARD_TOKENS:
                jobs = self._fetch_jobs(token)
                relevant = [j for j in jobs if self._is_relevant(j)]
                total_fetched += len(relevant)

                if relevant:
                    logger.info(
                        f"[greenhouse] '{token}' → "
                        f"{len(relevant)} offres pertinentes / {len(jobs)} total"
                    )

                for job in relevant:
                    # Enrichit les données avec le token source
                    job["board_token"] = token
                    if self._save_raw(job):
                        inserted += 1

        except requests.HTTPError as e:
            logger.error(f"[greenhouse] Erreur HTTP : {e}")
        except Exception as e:
            logger.error(f"[greenhouse] Erreur inattendue : {e}")
        finally:
            self.close()

        logger.info(
            f"[greenhouse] Collecte terminée : "
            f"{inserted} offres insérées / {total_fetched} pertinentes trouvées."
        )
        return inserted


if __name__ == "__main__":
    collector = GreenhouseCollector()
    collector.collect()
