import streamlit as st
import plotly.express as px
from src.dashboard.db import (
    get_overview_stats,
    get_offres_by_source,
    get_top_locations,
    get_contracts_distribution
)


def render():
    st.title("📈 Vue générale")
    st.caption("Aperçu global des offres collectées")

    # ── KPIs ──────────────────────────────────────────────────────────────────
    stats = get_overview_stats()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total offres", f"{int(stats.get('total_offres', 0)):,}")
    col2.metric("Sources", int(stats.get('nb_sources', 0)))
    col3.metric("Entreprises", f"{int(stats.get('nb_entreprises', 0)):,}")
    col4.metric("Période",
        f"{stats.get('date_min', 'N/A')} → {stats.get('date_max', 'N/A')}"
    )

    st.divider()

    # ── Répartition par source ─────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Offres par source")
        df_sources = get_offres_by_source()
        if not df_sources.empty:
            fig = px.pie(
                df_sources,
                values="nb_offres",
                names="source",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, width='stretch')

    # ── Types de contrats ──────────────────────────────────────────────────────
    with col_right:
        st.subheader("Types de contrats")
        df_contracts = get_contracts_distribution()
        if not df_contracts.empty:
            fig = px.bar(
                df_contracts.head(10),
                x="nb_offres",
                y="type_contrat",
                orientation="h",
                color="nb_offres",
                color_continuous_scale="Blues"
            )
            fig.update_layout(showlegend=False, yaxis_title="", xaxis_title="Nombre d'offres")
            st.plotly_chart(fig, width='stretch')

    # ── Top localisations ──────────────────────────────────────────────────────
    st.subheader("Top 15 localisations")
    df_locations = get_top_locations(15)
    if not df_locations.empty:
        fig = px.bar(
            df_locations,
            x="localisation",
            y="nb_offres",
            color="nb_offres",
            color_continuous_scale="Teal"
        )
        fig.update_layout(xaxis_title="", yaxis_title="Nombre d'offres")
        st.plotly_chart(fig, width='stretch')
