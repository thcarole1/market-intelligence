import streamlit as st
import plotly.express as px
from src.dashboard.db import get_top_skills, get_skills_by_source


def render():
    st.title("🛠️ Top Skills")
    st.caption("Compétences les plus demandées sur le marché Data Engineer")

    sources = st.session_state.get("selected_sources", [])

    # ── Contrôles ─────────────────────────────────────────────────────────────
    col1, col2 = st.columns([3, 1])
    with col2:
        limit = st.slider("Nombre de skills", 10, 50, 30)

    # ── Top skills global ──────────────────────────────────────────────────────
    df = get_top_skills(sources=sources, limit=limit)

    if df.empty:
        st.warning("Aucune donnée disponible pour les filtres sélectionnés.")
        return

    with col1:
        st.subheader(f"Top {limit} skills — {len(sources)} source(s)")

    fig = px.bar(
        df,
        x="total",
        y="skill",
        orientation="h",
        color="total",
        color_continuous_scale="Viridis",
        text="total"
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        xaxis_title="Nombre d'offres",
        yaxis_title="",
        showlegend=False,
        height=max(400, limit * 22)
    )
    st.plotly_chart(fig, width='stretch')

    st.divider()

    # ── Comparaison par source ─────────────────────────────────────────────────
    st.subheader("Comparaison par source — Top 15")
    df_by_source = get_skills_by_source()

    if not df_by_source.empty and sources:
        df_filtered = df_by_source[df_by_source["source"].isin(sources)]
        top_skills = df.head(15)["skill"].tolist()
        df_filtered = df_filtered[df_filtered["skill"].isin(top_skills)]

        fig2 = px.bar(
            df_filtered,
            x="skill",
            y="nb_offres",
            color="source",
            barmode="group",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig2.update_layout(
            xaxis_title="",
            yaxis_title="Nombre d'offres",
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Tableau brut ───────────────────────────────────────────────────────────
    with st.expander("Voir les données brutes"):
        st.dataframe(df, width='stretch')
