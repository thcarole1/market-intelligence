import logging
import feedparser
from src.ingestion.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class WWRCollector(BaseCollector):
    """
    Collecteur pour We Work Remotely via flux RSS publics.
    Pas d'authentification requise.
    """

    FEEDS = {
        "programming": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "devops":      "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
        "data":        "https://weworkremotely.com/categories/remote-data-science-jobs.rss",
    }

    def __init__(self) -> None:
        super().__init__(source_name="wwr")

    def _fetch_feed(self, category: str, url: str) -> list[dict]:
        """Parse un flux RSS et retourne une liste de dicts normalisés."""
        feed = feedparser.parse(url)

        if feed.bozo:
            logger.warning(f"[wwr] Flux mal formé pour '{category}' : {feed.bozo_exception}")

        jobs = []
        for entry in feed.entries:
            jobs.append({
                "title":      entry.get("title", ""),
                "company":    entry.get("author", ""),
                "link":       entry.get("link", ""),
                "published":  entry.get("published", ""),
                "summary":    entry.get("summary", ""),
                "category":   category,
                "source":     "wwr"
            })
        return jobs

    def collect(self) -> int:
        """
        Collecte les offres depuis tous les flux RSS WWR.
        Retourne le nombre d'offres insérées.
        """
        logger.info("[wwr] Démarrage collecte...")
        inserted = 0

        try:
            for category, url in self.FEEDS.items():
                logger.info(f"[wwr] Flux : '{category}'")
                jobs = self._fetch_feed(category, url)
                logger.info(f"[wwr] {len(jobs)} offres récupérées")

                for job in jobs:
                    if self._save_raw(job):
                        inserted += 1

        except Exception as e:
            logger.error(f"[wwr] Erreur inattendue : {e}")
        finally:
            self.close()

        logger.info(f"[wwr] Collecte terminée : {inserted} offres insérées.")
        return inserted


if __name__ == "__main__":
    collector = WWRCollector()
    collector.collect()
