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


from src.dashboard.db import get_regions, get_departements

# ── Filtres géographiques ──────────────────────────────────────────────────────
st.sidebar.divider()
st.sidebar.subheader("Géographie")

regions = get_regions()
selected_regions = st.sidebar.multiselect(
    "Régions",
    options=regions,
    default=[]
)

# Départements filtrés par région sélectionnée
if selected_regions:
    dept_df = get_departements(selected_regions[0]) if len(selected_regions) == 1 else get_departements()
else:
    dept_df = get_departements()

dept_options = [
    f"{row['dept_code']} - {row['dept_nom']}"
    for _, row in dept_df.iterrows()
]
selected_depts_raw = st.sidebar.multiselect(
    "Départements",
    options=dept_options,
    default=[]
)
selected_dept_codes = [d.split(" - ")[0] for d in selected_depts_raw]

include_remote = st.sidebar.checkbox("Inclure les offres Remote", value=True)

# Stocke en session_state
st.session_state["selected_regions"] = selected_regions
st.session_state["selected_dept_codes"] = selected_dept_codes
st.session_state["include_remote"] = include_remote

# ── Rendu de la page sélectionnée ─────────────────────────────────────────────
PAGES[selection].render()
