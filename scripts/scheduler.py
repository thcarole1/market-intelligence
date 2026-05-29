"""
Orchestrateur du pipeline Market Intelligence.
Remplace Airflow pour un contexte solo/laptop.
Lance le pipeline complet selon un planning configurable.
"""
import logging
import subprocess
import sys
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# Racine du projet
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from src.config import settings, logger

scheduler = BlockingScheduler()


def run_collectors() -> bool:
    """Lance tous les collecteurs en séquence."""
    collectors = [
        "src.ingestion.france_travail_collector",
        "src.ingestion.remotive_collector",
        "src.ingestion.wwr_collector",
        "src.ingestion.greenhouse_collector",
        "src.ingestion.hellowork_collector",
    ]

    for module in collectors:
        logger.info(f"[scheduler] Lancement : {module}")
        result = subprocess.run(
            [sys.executable, "-m", module],
            cwd=ROOT,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logger.error(f"[scheduler] Échec : {module}\n{result.stderr}")
            return False
        logger.info(f"[scheduler] Succès : {module}")

    return True


def run_dbt() -> bool:
    """Lance dbt run pour mettre à jour les couches Silver et Gold."""
    logger.info("[scheduler] Lancement dbt run...")
    result = subprocess.run(
        ["dbt", "run"],
        cwd=ROOT / "dbt" / "market_intelligence",
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        logger.error(f"[scheduler] dbt run échoué\n{result.stderr}")
        return False
    logger.info("[scheduler] dbt run terminé ✅")
    return True


def run_skills_extraction() -> bool:
    """Lance l'extraction NLP des skills."""
    logger.info("[scheduler] Extraction NLP skills...")
    result = subprocess.run(
        [sys.executable, "-m", "src.ingestion.skills_extractor"],
        cwd=ROOT,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        logger.error(f"[scheduler] Extraction NLP échouée\n{result.stderr}")
        return False
    logger.info("[scheduler] Extraction NLP terminée ✅")
    return True


def run_pipeline() -> None:
    """
    Pipeline complet :
    1. Collecteurs (toutes sources)
    2. dbt run (Silver + Gold)
    3. Extraction NLP skills
    """
    logger.info("=" * 60)
    logger.info("[scheduler] DÉMARRAGE PIPELINE COMPLET")
    logger.info("=" * 60)

    if not run_collectors():
        logger.error("[scheduler] Pipeline arrêté — échec collecteurs")
        return

    if not run_dbt():
        logger.error("[scheduler] Pipeline arrêté — échec dbt")
        return

    if not run_skills_extraction():
        logger.error("[scheduler] Pipeline arrêté — échec NLP")
        return

    logger.info("=" * 60)
    logger.info("[scheduler] PIPELINE TERMINÉ ✅")
    logger.info("=" * 60)


# ── Planning ───────────────────────────────────────────────────────────────────
# Toutes les nuits à 2h00
scheduler.add_job(
    run_pipeline,
    trigger=CronTrigger(hour=2, minute=0),
    id="market_intelligence_pipeline",
    name="Market Intelligence Pipeline",
    replace_existing=True
)

logger.info("[scheduler] Scheduler démarré — pipeline à 02:00 chaque nuit")
logger.info("[scheduler] Appuie sur Ctrl+C pour arrêter")


if __name__ == "__main__":
    # Lance le pipeline immédiatement au démarrage (optionnel)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--now", action="store_true", help="Lance le pipeline immédiatement")
    args = parser.parse_args()

    if args.now:
        logger.info("[scheduler] Lancement immédiat demandé")
        run_pipeline()
    else:
        try:
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("[scheduler] Arrêt du scheduler")
            scheduler.shutdown()
