import streamlit as st

# Configuration de la page — doit être le premier appel Streamlit
st.set_page_config(
    page_title="Market Intelligence — Data Engineer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import des pages
from src.dashboard.views import overview, skills, cooccurrences

# ── Navigation ────────────────────────────────────────────────────────────────
PAGES = {
    "📈 Vue générale":       overview,
    "🛠️ Top Skills":         skills,
    "🔗 Co-occurrences":     cooccurrences,
}

st.sidebar.title("📊 Market Intelligence")
st.sidebar.caption("Data Engineer — France")
st.sidebar.divider()

selection = st.sidebar.radio("Navigation", list(PAGES.keys()))

# ── Filtres globaux ────────────────────────────────────────────────────────────
st.sidebar.divider()
st.sidebar.subheader("Filtres")

SOURCES = ["france_travail", "hellowork", "remotive", "wwr", "greenhouse"]

selected_sources = st.sidebar.multiselect(
    "Sources",
    options=SOURCES,
    default=SOURCES
)

# Stocke les filtres en session_state pour les pages
st.session_state["selected_sources"] = selected_sources

st.sidebar.divider()
st.sidebar.caption("Pipeline : France Travail · HelloWork · Remotive · WWR · Greenhouse")

# ── Rendu de la page sélectionnée ─────────────────────────────────────────────
PAGES[selection].render()
