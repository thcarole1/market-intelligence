import logging
import requests
from bs4 import BeautifulSoup
from requests_ratelimiter import LimiterSession
from src.ingestion.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class HelloworkCollector(BaseCollector):
    """
    Collecteur pour HelloWork via scraping HTML.
    Utilise les attributs data-cy stables pour le parsing.
    """

    BASE_URL = "https://www.hellowork.com"
    SEARCH_URL = f"{BASE_URL}/fr-fr/emploi/recherche.html"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "fr-FR,fr;q=0.9",
    }
    KEYWORDS = ["data engineer", "data engineering"]

    def __init__(self) -> None:
        super().__init__(source_name="hellowork")
        self.session = LimiterSession(per_second=1)
        self.session.headers.update(self.HEADERS)

    def _fetch_page(self, keyword: str, page: int) -> BeautifulSoup | None:
        """Récupère et parse une page de résultats."""
        params = {
            "k": keyword,
            "l": "France",
            "p": page,
        }
        response = self.session.get(self.SEARCH_URL, params=params, timeout=30)

        if response.status_code == 404 or not response.text.strip():
            return None

        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")

    def _parse_jobs(self, soup: BeautifulSoup, keyword: str) -> list[dict]:
        """Extrait les offres via les attributs data-cy stables."""
        jobs = []
        cards = soup.find_all("li", attrs={"data-id-storage-item-id": True})

        for card in cards:
            try:
                offer_id = card.get("data-id-storage-item-id", "")
                link_tag = card.find("a", attrs={"data-cy": "offerTitle"})
                location_tag = card.find(attrs={"data-cy": "localisationCard"})
                contract_tag = card.find(attrs={"data-cy": "contractCard"})

                if not link_tag:
                    continue

                # Titre et entreprise depuis le h3 dans le lien
                h3 = link_tag.find("h3")
                paragraphs = h3.find_all("p") if h3 else []
                title   = paragraphs[0].text.strip() if len(paragraphs) > 0 else ""
                company = paragraphs[1].text.strip() if len(paragraphs) > 1 else ""

                jobs.append({
                    "offer_id":   offer_id,
                    "title":      title,
                    "company":    company,
                    "location":   location_tag.text.strip() if location_tag else "",
                    "contract":   contract_tag.text.strip() if contract_tag else "",
                    "url":        f"{self.BASE_URL}{link_tag['href']}",
                    "aria_label": link_tag.get("aria-label", ""),
                    "keyword":    keyword,
                    "source":     "hellowork"
                })
            except Exception as e:
                logger.warning(f"[hellowork] Erreur parsing carte : {e}")
                continue

        return jobs

    def _has_next_page(self, soup: BeautifulSoup, current_page: int) -> bool:
        """Vérifie s'il existe une page suivante."""
        next_btn = soup.find("button", attrs={"value": str(current_page + 1)})
        return next_btn is not None

    def collect(self) -> int:
        """
        Collecte les offres HelloWork pour chaque keyword.
        Retourne le nombre d'offres insérées.
        """
        logger.info("[hellowork] Démarrage collecte...")
        inserted = 0

        try:
            for keyword in self.KEYWORDS:
                logger.info(f"[hellowork] Keyword : '{keyword}'")
                page = 1

                while True:
                    logger.info(f"[hellowork] Page {page}")
                    soup = self._fetch_page(keyword, page)

                    if soup is None:
                        logger.info(f"[hellowork] Fin des résultats.")
                        break

                    jobs = self._parse_jobs(soup, keyword)

                    if not jobs:
                        logger.info(f"[hellowork] Aucune offre page {page} — arrêt.")
                        break

                    for job in jobs:
                        if self._save_raw(job):
                            inserted += 1

                    if not self._has_next_page(soup, page):
                        logger.info(f"[hellowork] Dernière page atteinte.")
                        break

                    page += 1

        except requests.HTTPError as e:
            logger.error(f"[hellowork] Erreur HTTP : {e}")
        except Exception as e:
            logger.error(f"[hellowork] Erreur inattendue : {e}")
        finally:
            self.close()

        logger.info(f"[hellowork] Collecte terminée : {inserted} offres insérées.")
        return inserted


if __name__ == "__main__":
    collector = HelloworkCollector()
    collector.collect()
