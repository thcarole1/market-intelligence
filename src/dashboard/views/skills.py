import streamlit as st
import plotly.express as px

from src.dashboard.db import (
    get_top_hard_skills,
    get_top_soft_skills,
    get_skills_by_source
)

def render():
    st.title("🛠️ Top Skills")
    st.caption("Compétences les plus demandées sur le marché Data Engineer")

    sources     = st.session_state.get("selected_sources", [])
    regions     = st.session_state.get("selected_regions", [])
    dept_codes  = st.session_state.get("selected_dept_codes", [])
    incl_remote = st.session_state.get("include_remote", True)

    geo_label = ""
    if regions:
        geo_label = f" — {', '.join(regions)}"
    elif dept_codes:
        geo_label = f" — depts {', '.join(dept_codes)}"

    col1, col2 = st.columns([3, 1])
    with col2:
        hard_limit = st.slider("Nombre de hard skills", 10, 50, 30)
        soft_limit = st.slider("Nombre de soft skills", 5, 20, 10)

    # ── Hard Skills ────────────────────────────────────────────────────────────
    with col1:
        st.subheader(f"⚙️ Top {hard_limit} Hard Skills{geo_label}")

    df_hard = get_top_hard_skills(
        sources=sources or None,
        regions=regions or None,
        dept_codes=dept_codes or None,
        include_remote=incl_remote,
        limit=hard_limit
    )

    if df_hard.empty:
        st.warning("Aucun hard skill pour les filtres sélectionnés.")
    else:
        fig_hard = px.bar(
            df_hard,
            x="total",
            y="skill",
            orientation="h",
            color="total",
            color_continuous_scale="Viridis",
            text="total"
        )
        fig_hard.update_traces(textposition="outside")
        fig_hard.update_layout(
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Nombre d'offres",
            yaxis_title="",
            showlegend=False,
            height=max(400, hard_limit * 22)
        )
        st.plotly_chart(fig_hard, width='stretch')

        with st.expander("Voir les données brutes — Hard Skills"):
            st.dataframe(df_hard, width='stretch')

    st.divider()

    # ── Soft Skills ────────────────────────────────────────────────────────────
    st.subheader(f"🤝 Top {soft_limit} Soft Skills{geo_label}")

    df_soft = get_top_soft_skills(
        sources=sources or None,
        regions=regions or None,
        dept_codes=dept_codes or None,
        include_remote=incl_remote,
        limit=soft_limit
    )

    if df_soft.empty:
        st.warning("Aucun soft skill pour les filtres sélectionnés.")
    else:
        fig_soft = px.bar(
            df_soft,
            x="total",
            y="skill",
            orientation="h",
            color="total",
            color_continuous_scale="Teal",
            text="total"
        )
        fig_soft.update_traces(textposition="outside")
        fig_soft.update_layout(
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Nombre d'offres",
            yaxis_title="",
            showlegend=False,
            height=max(300, soft_limit * 40)
        )
        st.plotly_chart(fig_soft, width='stretch')

        with st.expander("Voir les données brutes — Soft Skills"):
            st.dataframe(df_soft, width='stretch')

    # ── Comparaison par source ─────────────────────────────────────────────────
    st.divider()
    st.subheader("📊 Comparaison hard skills par source")
    df_by_source = get_skills_by_source()

    if not df_by_source.empty and sources:
        df_filtered = df_by_source[
            (df_by_source["source"].isin(sources)) &
            (df_by_source["skill_type"] == "hard")
        ]
        top_skills = df_hard.head(15)["skill"].tolist() if not df_hard.empty else []
        df_filtered = df_filtered[df_filtered["skill"].isin(top_skills)]

        if not df_filtered.empty:
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
            st.plotly_chart(fig2, width='stretch')
