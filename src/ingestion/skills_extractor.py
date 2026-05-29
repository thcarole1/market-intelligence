import logging
import re
import spacy
import psycopg2
from psycopg2.extras import execute_values
from src.config import settings
from src.ingestion.skills_dictionary import HARD_SKILLS_INDEX, SOFT_SKILLS_INDEX

logger = logging.getLogger(__name__)

# Charge les modèles spaCy une seule fois
try:
    nlp_fr = spacy.load("fr_core_news_sm")
    nlp_en = spacy.load("en_core_web_sm")
except OSError as e:
    logger.error(f"Modèle spaCy manquant : {e}")
    raise


def detect_language(text: str) -> str:
    """Détection simple de la langue via mots-clés fréquents."""
    french_markers = ["expérience", "poste", "entreprise", "nous", "votre", "équipe"]
    text_lower = text.lower()
    fr_count = sum(1 for w in french_markers if w in text_lower)
    return "fr" if fr_count >= 2 else "en"


def extract_skills_from_text(text: str) -> list[tuple[str, str]]:
    """
    Extrait les skills depuis un texte brut.
    Retourne une liste de (skill_normalisé, type) : ('python', 'hard')
    """
    if not text or len(text.strip()) < 10:
        return []

    text_lower = text.lower()
    found_skills = {}

    # Détecte la langue et charge le bon modèle
    lang = detect_language(text_lower)
    nlp = nlp_fr if lang == "fr" else nlp_en

    # Nettoyage léger du texte
    text_clean = re.sub(r'<[^>]+>', ' ', text_lower)  # retire HTML
    text_clean = re.sub(r'\s+', ' ', text_clean).strip()

    # Ajoute cette ligne — corrige l'encodage latin1 mal interprété
    try:
        text_clean = text_clean.encode('latin1').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass  # texte déjà correct, on laisse tel quel

    # Recherche des variantes dans le texte
    for variant, skill in HARD_SKILLS_INDEX.items():
        pattern = r'(?<![a-z])' + re.escape(variant) + r'(?![a-z])'
        if re.search(pattern, text_clean):
            found_skills[skill] = 'hard'

    for variant, skill in SOFT_SKILLS_INDEX.items():
        pattern = r'(?<![a-z])' + re.escape(variant) + r'(?![a-z])'
        if re.search(pattern, text_clean):
            found_skills[skill] = 'soft'

    return list(found_skills.items())


def extract_and_store_skills(batch_size: int = 100) -> int:
    """
    Extrait les skills de toutes les offres non encore traitées.
    Retourne le nombre d'offres traitées.
    """
    logger.info("[skills_extractor] Démarrage extraction NLP...")

    conn = psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password
    )

    try:
        with conn.cursor() as cur:
            # Récupère les offres sans skills extraits
            cur.execute("""
                SELECT r.id, r.source, r.raw_data
                FROM raw_jobs r
                LEFT JOIN job_skills js ON r.id = js.raw_job_id
                WHERE js.raw_job_id IS NULL
                LIMIT %s
            """, (batch_size,))
            jobs = cur.fetchall()

        if not jobs:
            logger.info("[skills_extractor] Aucune offre à traiter.")
            return 0

        logger.info(f"[skills_extractor] {len(jobs)} offres à traiter...")
        processed = 0

        for job_id, source, raw_data in jobs:
            # Construit le texte à analyser selon la source
            text_parts = []

            if source == "france_travail":
                text_parts = [
                    raw_data.get("intitule", ""),
                    raw_data.get("description", "")
                ]
            elif source == "hellowork":
                text_parts = [
                    raw_data.get("title", ""),
                    raw_data.get("aria_label", "")
                ]
            elif source == "remotive":
                text_parts = [
                    raw_data.get("title", ""),
                    raw_data.get("description", ""),
                    raw_data.get("tags", "")
                ]
            elif source == "wwr":
                text_parts = [
                    raw_data.get("title", ""),
                    raw_data.get("summary", "")
                ]
            elif source == "greenhouse":
                text_parts = [
                    raw_data.get("title", ""),
                    raw_data.get("content", "")
                ]

            full_text = " ".join(str(p) for p in text_parts if p)
            skills = extract_skills_from_text(full_text)

            if skills:
                rows = [(job_id, skill, skill_type) for skill, skill_type in skills]
                with conn.cursor() as cur:
                    execute_values(cur, """
                        INSERT INTO job_skills (raw_job_id, skill, skill_type)
                        VALUES %s
                        ON CONFLICT (raw_job_id, skill) DO NOTHING
                    """, rows)
                conn.commit()

            processed += 1
            if processed % 100 == 0:
                logger.info(f"[skills_extractor] {processed}/{len(jobs)} offres traitées...")

        logger.info(f"[skills_extractor] Extraction terminée : {processed} offres traitées.")
        return processed

    except Exception as e:
        conn.rollback()
        logger.error(f"[skills_extractor] Erreur : {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    extract_and_store_skills(batch_size=2054)
