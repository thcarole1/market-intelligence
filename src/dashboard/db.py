from sqlalchemy import create_engine
from src.config import settings
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def get_engine():
    """Moteur SQLAlchemy — compatible pandas."""
    url = (
        f"postgresql+psycopg2://{settings.postgres_user}:"
        f"{settings.postgres_password}@localhost:"
        f"{settings.postgres_port}/{settings.postgres_db}"
    )
    return create_engine(url)


def query(sql: str, params: dict = None) -> pd.DataFrame:
    """Exécute une requête et retourne un DataFrame."""
    try:
        with get_engine().connect() as conn:
            return pd.read_sql_query(sql, conn, params=params)
    except Exception as e:
        logger.error(f"Erreur requête : {e}")
        return pd.DataFrame()


# ── Requêtes Gold ─────────────────────────────────────────────────────────────

def get_top_skills(sources: list[str] = None, limit: int = 30) -> pd.DataFrame:
    """Top skills toutes sources ou filtrées."""
    if sources:
        placeholders = ",".join(["%s"] * len(sources))
        sql = f"""
            SELECT skill, SUM(nb_offres) as total
            FROM public_gold.skills_freq
            WHERE source IN ({placeholders})
            GROUP BY skill
            ORDER BY total DESC
            LIMIT %s
        """
        return query(sql, tuple(sources) + (limit,))
    else:
        sql = """
            SELECT skill, SUM(nb_offres) as total
            FROM public_gold.skills_freq
            GROUP BY skill
            ORDER BY total DESC
            LIMIT %s
        """
        return query(sql, (limit,))


def get_skills_by_source() -> pd.DataFrame:
    """Skills par source pour comparaison."""
    sql = """
        SELECT source, skill, nb_offres, pct_offres
        FROM public_gold.skills_freq
        ORDER BY source, nb_offres DESC
    """
    return query(sql)


def get_top_cooccurrences(sources: list[str] = None, limit: int = 30) -> pd.DataFrame:
    """Top co-occurrences de skills."""
    if sources:
        placeholders = ",".join(["%s"] * len(sources))
        sql = f"""
            SELECT skill_a, skill_b, SUM(nb_offres) as total
            FROM public_gold.co_occurrences
            WHERE source IN ({placeholders})
            GROUP BY skill_a, skill_b
            ORDER BY total DESC
            LIMIT %s
        """
        return query(sql, tuple(sources) + (limit,))
    else:
        sql = """
            SELECT skill_a, skill_b, SUM(nb_offres) as total
            FROM public_gold.co_occurrences
            GROUP BY skill_a, skill_b
            ORDER BY total DESC
            LIMIT %s
        """
        return query(sql, (limit,))


def get_overview_stats() -> dict:
    """Statistiques générales pour la page d'accueil."""
    sql = """
        SELECT
            COUNT(*)                            AS total_offres,
            COUNT(DISTINCT source)              AS nb_sources,
            COUNT(DISTINCT entreprise)          AS nb_entreprises,
            MIN(date_publication)               AS date_min,
            MAX(date_publication)               AS date_max
        FROM public_silver.jobs
    """
    df = query(sql)
    return df.iloc[0].to_dict() if not df.empty else {}


def get_offres_by_source() -> pd.DataFrame:
    """Répartition des offres par source."""
    sql = """
        SELECT source, COUNT(*) as nb_offres
        FROM public_silver.jobs
        GROUP BY source
        ORDER BY nb_offres DESC
    """
    return query(sql)


def get_top_locations(limit: int = 15) -> pd.DataFrame:
    """Villes les plus demandeuses."""
    sql = """
        SELECT localisation, COUNT(*) as nb_offres
        FROM public_silver.jobs
        WHERE localisation IS NOT NULL
          AND localisation != ''
        GROUP BY localisation
        ORDER BY nb_offres DESC
        LIMIT %s
    """
    return query(sql, (limit,))


def get_contracts_distribution() -> pd.DataFrame:
    """Répartition des types de contrats."""
    sql = """
        SELECT type_contrat, COUNT(*) as nb_offres
        FROM public_silver.jobs
        WHERE type_contrat IS NOT NULL
          AND type_contrat != ''
        GROUP BY type_contrat
        ORDER BY nb_offres DESC
    """
    return query(sql)
