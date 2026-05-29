"""
Module de monitoring du pipeline Market Intelligence.
Enregistre les métriques de chaque run et détecte les anomalies.
"""
import json
import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import psycopg2
from psycopg2.extras import Json

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SourceMetric:
    """Métriques pour une source de données."""
    source: str
    nb_collected: int = 0
    nb_inserted: int = 0
    nb_duplicates: int = 0
    status: str = "success"
    error_message: Optional[str] = None


@dataclass
class PipelineRun:
    """Suivi d'une exécution complète du pipeline."""
    start_time: float = field(default_factory=time.time)
    status: str = "success"
    source_metrics: list[SourceMetric] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        return round(time.time() - self.start_time, 2)

    def add_source_metric(self, metric: SourceMetric) -> None:
        self.source_metrics.append(metric)
        if metric.status == "failure":
            self.status = "partial"

    def add_error(self, error: str) -> None:
        self.errors.append(error)
        self.status = "failure"


def _get_connection():
    return psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password
    )


def save_pipeline_run(run: PipelineRun) -> int:
    """Persiste les métriques du pipeline en base. Retourne le run_id."""
    details = {
        "errors": run.errors,
        "sources": [
            {
                "source": m.source,
                "nb_collected": m.nb_collected,
                "nb_inserted": m.nb_inserted,
                "nb_duplicates": m.nb_duplicates,
                "status": m.status,
                "error_message": m.error_message
            }
            for m in run.source_metrics
        ]
    }

    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO pipeline_runs (status, duration_seconds, details)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (run.status, run.duration_seconds, Json(details)))
            run_id = cur.fetchone()[0]

            for metric in run.source_metrics:
                cur.execute("""
                    INSERT INTO source_metrics
                        (run_id, source, nb_collected, nb_inserted,
                         nb_duplicates, status, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    run_id, metric.source, metric.nb_collected,
                    metric.nb_inserted, metric.nb_duplicates,
                    metric.status, metric.error_message
                ))

        conn.commit()
        logger.info(f"[monitoring] Run #{run_id} sauvegardé — status: {run.status}")
        return run_id

    except Exception as e:
        conn.rollback()
        logger.error(f"[monitoring] Erreur sauvegarde run : {e}")
        return -1
    finally:
        conn.close()


def check_data_quality() -> dict:
    """
    Vérifie la qualité des données en base.
    Retourne un rapport avec les anomalies détectées.
    """
    conn = _get_connection()
    report = {"status": "ok", "anomalies": [], "metrics": {}}

    try:
        with conn.cursor() as cur:
            # Offres par source
            cur.execute("""
                SELECT source, COUNT(*) as nb
                FROM raw_jobs
                GROUP BY source
                ORDER BY nb DESC
            """)
            sources = {row[0]: row[1] for row in cur.fetchall()}
            report["metrics"]["offres_par_source"] = sources

            # Détecte les sources avec 0 offres
            expected_sources = [
                "france_travail", "hellowork", "remotive", "wwr", "greenhouse"
            ]
            for source in expected_sources:
                if sources.get(source, 0) == 0:
                    report["anomalies"].append(
                        f"⚠️ Source '{source}' : 0 offres collectées"
                    )

            # Offres Silver
            cur.execute("SELECT COUNT(*) FROM public_silver.jobs")
            nb_silver = cur.fetchone()[0]
            report["metrics"]["offres_silver"] = nb_silver

            if nb_silver == 0:
                report["anomalies"].append("🚨 Couche Silver vide !")

            # Skills extraits
            cur.execute("""
                SELECT COUNT(DISTINCT raw_job_id) as offres_avec_skills,
                       COUNT(*) as total_skills
                FROM job_skills
            """)
            row = cur.fetchone()
            report["metrics"]["offres_avec_skills"] = row[0]
            report["metrics"]["total_skills"] = row[1]

            if row[0] == 0:
                report["anomalies"].append("⚠️ Aucun skill extrait")

            # Dernier run pipeline
            cur.execute("""
                SELECT status, run_at, duration_seconds
                FROM pipeline_runs
                ORDER BY run_at DESC
                LIMIT 1
            """)
            last_run = cur.fetchone()
            if last_run:
                report["metrics"]["dernier_run"] = {
                    "status": last_run[0],
                    "date": str(last_run[1]),
                    "duree_secondes": last_run[2]
                }

        if report["anomalies"]:
            report["status"] = "warning"

    except Exception as e:
        report["status"] = "error"
        report["anomalies"].append(f"Erreur monitoring : {e}")
    finally:
        conn.close()

    return report


def print_monitoring_report() -> None:
    """Affiche un rapport de monitoring lisible en console."""
    report = check_data_quality()

    print("\n" + "=" * 60)
    print("📊 RAPPORT DE MONITORING — Market Intelligence")
    print("=" * 60)

    status_icon = {"ok": "✅", "warning": "⚠️", "error": "🚨"}
    print(f"Status global : {status_icon.get(report['status'], '?')} {report['status'].upper()}")

    print("\n📈 Métriques :")
    metrics = report.get("metrics", {})

    if "offres_par_source" in metrics:
        print("  Offres par source :")
        for source, nb in metrics["offres_par_source"].items():
            print(f"    {source:20s} : {nb:>6,} offres")

    print(f"  Offres Silver     : {metrics.get('offres_silver', 0):>6,}")
    print(f"  Offres avec skills: {metrics.get('offres_avec_skills', 0):>6,}")
    print(f"  Total skills      : {metrics.get('total_skills', 0):>6,}")

    if "dernier_run" in metrics:
        run = metrics["dernier_run"]
        print(f"\n🕐 Dernier pipeline :")
        print(f"  Date   : {run['date']}")
        print(f"  Status : {run['status']}")
        print(f"  Durée  : {run['duree_secondes']}s")

    if report["anomalies"]:
        print(f"\n⚠️  Anomalies détectées ({len(report['anomalies'])}) :")
        for anomaly in report["anomalies"]:
            print(f"  {anomaly}")
    else:
        print("\n✅ Aucune anomalie détectée")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    print_monitoring_report()
