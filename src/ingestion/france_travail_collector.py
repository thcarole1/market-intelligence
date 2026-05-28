import logging
import requests
from src.config import settings
from src.ingestion.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class FranceTravailCollector(BaseCollector):
    """
    Collecteur pour l'API France Travail (ex-Pôle Emploi).
    Authentification OAuth2, pagination automatique.
    """

    AUTH_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
    SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"

    def __init__(self) -> None:
        super().__init__(source_name="france_travail")
        self.token: str | None = None

    def _get_token(self) -> str:
        """Authentification OAuth2 — token valable 30 minutes."""
        logger.info("[france_travail] Authentification OAuth2...")
        response = requests.post(
            self.AUTH_URL,
            params={"realm": "/partenaire"},
            data={
                "grant_type": "client_credentials",
                "client_id": settings.francetravail_client_id,
                "client_secret": settings.francetravail_client_secret,
                "scope": "api_offresdemploiv2 o2dsoffre"
            }
        )
        response.raise_for_status()
        logger.info("[france_travail] Token obtenu ✅")
        return response.json()["access_token"]

    def _fetch_page(self, keyword: str, start: int) -> dict:
        """Récupère une page de 150 offres maximum."""
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {
            "motsCles": keyword,
            "range": f"{start}-{start + 149}",
        }
        response = requests.get(
            self.SEARCH_URL,
            headers=headers,
            params=params
        )

        # L'API retourne 206 avec du contenu, ou 204 sans contenu
        if response.status_code == 204 or not response.text.strip():
            logger.info("[france_travail] Réponse vide — fin des résultats.")
            return {}

        response.raise_for_status()
        return response.json()

    def collect(self, keyword: str = "data engineer") -> int:
        """
        Collecte toutes les offres pour un mot-clé donné.
        Retourne le nombre d'offres insérées.
        """
        logger.info(f"[france_travail] Démarrage collecte : '{keyword}'")

        self.token = self._get_token()

        inserted = 0
        start = 0

        try:
            while True:
                logger.info(f"[france_travail] Récupération offres {start} → {start + 149}")
                data = self._fetch_page(keyword, start)
                offres = data.get("resultats", [])

                if not offres:
                    logger.info("[france_travail] Plus d'offres disponibles.")
                    break

                for offre in offres:
                    if self._save_raw(offre):
                        inserted += 1

                if start + 150 >= 1000:
                    break

                start += 150

        except requests.HTTPError as e:
            logger.error(f"[france_travail] Erreur API : {e}")
        except Exception as e:
            logger.error(f"[france_travail] Erreur inattendue : {e}")
        finally:
            self.close()

        logger.info(f"[france_travail] Collecte terminée : {inserted} offres insérées.")
        return inserted


if __name__ == "__main__":
    collector = FranceTravailCollector()
    collector.collect(keyword="data engineer")
