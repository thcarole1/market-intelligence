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
            if params:
                from sqlalchemy import text
                return pd.read_sql_query(text(sql), conn, params=params)
            return pd.read_sql_query(sql, conn)
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
    sql = """
        SELECT source, skill, skill_type, nb_offres, pct_offres
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
    sql = """
        SELECT source, COUNT(*) as nb_offres
        FROM public_silver.jobs
        GROUP BY source
        ORDER BY nb_offres DESC
    """
    return query(sql)


def get_top_locations(limit: int = 15) -> pd.DataFrame:
    sql = """
        SELECT localisation, COUNT(*) as nb_offres
        FROM public_silver.jobs
        WHERE localisation IS NOT NULL
          AND localisation != ''
        GROUP BY localisation
        ORDER BY nb_offres DESC
        LIMIT :limit
    """
    return query(sql, {"limit": limit})


def get_contracts_distribution() -> pd.DataFrame:
    sql = """
        SELECT type_contrat, COUNT(*) as nb_offres
        FROM public_silver.jobs
        WHERE type_contrat IS NOT NULL
          AND type_contrat != ''
        GROUP BY type_contrat
        ORDER BY nb_offres DESC
    """
    return query(sql)


def get_regions() -> list[str]:
    """Liste des régions disponibles."""
    sql = """
        SELECT DISTINCT region_nom
        FROM public_silver.jobs
        WHERE region_nom IS NOT NULL
        ORDER BY region_nom
    """
    df = query(sql)
    return df["region_nom"].tolist() if not df.empty else []


def get_departements(region: str = None) -> pd.DataFrame:
    """Liste des départements, filtrés par région si fournie."""
    if region:
        sql = """
            SELECT DISTINCT dept_code, dept_nom
            FROM public_silver.jobs
            WHERE region_nom = :region
              AND dept_code IS NOT NULL
            ORDER BY dept_code
        """
        df = query(sql, {"region": region})
    else:
        sql = """
            SELECT DISTINCT dept_code, dept_nom
            FROM public_silver.jobs
            WHERE dept_code IS NOT NULL
            ORDER BY dept_code
        """
        df = query(sql)
    return df


def get_top_skills_geo(
    sources: list[str] = None,
    regions: list[str] = None,
    dept_codes: list[str] = None,
    include_remote: bool = True,
    limit: int = 30
) -> pd.DataFrame:
    """Top skills avec filtres géographiques."""
    conditions = ["1=1"]
    params = {}

    if sources:
        conditions.append("source = ANY(:sources)")
        params["sources"] = sources

    if regions:
        conditions.append("region_nom = ANY(:regions)")
        params["regions"] = regions

    if dept_codes:
        conditions.append("dept_code = ANY(:dept_codes)")
        params["dept_codes"] = dept_codes

    if not include_remote:
        conditions.append("is_remote = FALSE")

    where = " AND ".join(conditions)

    sql = f"""
        SELECT skill, skill_type, SUM(nb_offres) as total
        FROM public_gold.skills_freq
        WHERE {where}
        GROUP BY skill, skill_type
        ORDER BY total DESC
        LIMIT :limit
    """
    params["limit"] = limit
    return query(sql, params)


def get_top_cooccurrences_geo(
    sources: list[str] = None,
    regions: list[str] = None,
    dept_codes: list[str] = None,
    include_remote: bool = True,
    limit: int = 50
) -> pd.DataFrame:
    """Co-occurrences avec filtres géographiques."""
    conditions = ["1=1"]
    params = {}

    if sources:
        conditions.append("source = ANY(:sources)")
        params["sources"] = sources

    if regions:
        conditions.append("region_nom = ANY(:regions)")
        params["regions"] = regions

    if dept_codes:
        conditions.append("dept_code = ANY(:dept_codes)")
        params["dept_codes"] = dept_codes

    if not include_remote:
        conditions.append("is_remote = FALSE")

    where = " AND ".join(conditions)

    sql = f"""
        SELECT skill_a, skill_b, SUM(nb_offres) as total
        FROM public_gold.co_occurrences
        WHERE {where}
        GROUP BY skill_a, skill_b
        ORDER BY total DESC
        LIMIT :limit
    """
    params["limit"] = limit
    return query(sql, params)

def get_top_hard_skills(
    sources: list[str] = None,
    regions: list[str] = None,
    dept_codes: list[str] = None,
    include_remote: bool = True,
    limit: int = 30
) -> pd.DataFrame:
    """Top hard skills uniquement."""
    conditions = ["skill_type = 'hard'"]
    params = {}

    if sources:
        conditions.append("source = ANY(:sources)")
        params["sources"] = sources
    if regions:
        conditions.append("region_nom = ANY(:regions)")
        params["regions"] = regions
    if dept_codes:
        conditions.append("dept_code = ANY(:dept_codes)")
        params["dept_codes"] = dept_codes
    if not include_remote:
        conditions.append("is_remote = FALSE")

    where = " AND ".join(conditions)
    sql = f"""
        SELECT skill, SUM(nb_offres) as total
        FROM public_gold.skills_freq
        WHERE {where}
        GROUP BY skill
        ORDER BY total DESC
        LIMIT :limit
    """
    params["limit"] = limit
    return query(sql, params)


def get_top_soft_skills(
    sources: list[str] = None,
    regions: list[str] = None,
    dept_codes: list[str] = None,
    include_remote: bool = True,
    limit: int = 20
) -> pd.DataFrame:
    """Top soft skills uniquement."""
    conditions = ["skill_type = 'soft'"]
    params = {}

    if sources:
        conditions.append("source = ANY(:sources)")
        params["sources"] = sources
    if regions:
        conditions.append("region_nom = ANY(:regions)")
        params["regions"] = regions
    if dept_codes:
        conditions.append("dept_code = ANY(:dept_codes)")
        params["dept_codes"] = dept_codes
    if not include_remote:
        conditions.append("is_remote = FALSE")

    where = " AND ".join(conditions)
    sql = f"""
        SELECT skill, SUM(nb_offres) as total
        FROM public_gold.skills_freq
        WHERE {where}
        GROUP BY skill
        ORDER BY total DESC
        LIMIT :limit
    """
    params["limit"] = limit
    return query(sql, params)
