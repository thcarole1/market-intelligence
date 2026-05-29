import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.dashboard.db import get_top_cooccurrences_geo

def render():
    # ... début inchangé ...
    sources    = st.session_state.get("selected_sources", [])
    regions    = st.session_state.get("selected_regions", [])
    dept_codes = st.session_state.get("selected_dept_codes", [])
    incl_remote = st.session_state.get("include_remote", True)

    df = get_top_cooccurrences_geo(
        sources=sources or None,
        regions=regions or None,
        dept_codes=dept_codes or None,
        include_remote=incl_remote,
        limit=50
    )

    if df.empty:
        st.warning("Aucune donnée disponible.")
        return

    # ── Heatmap ────────────────────────────────────────────────────────────────
    st.subheader("Heatmap des co-occurrences")

    top_skills = list(set(
        df.head(20)["skill_a"].tolist() +
        df.head(20)["skill_b"].tolist()
    ))

    matrix = pd.DataFrame(0, index=top_skills, columns=top_skills)
    for _, row in df.iterrows():
        if row["skill_a"] in top_skills and row["skill_b"] in top_skills:
            matrix.loc[row["skill_a"], row["skill_b"]] = row["total"]
            matrix.loc[row["skill_b"], row["skill_a"]] = row["total"]

    fig = px.imshow(
        matrix,
        color_continuous_scale="Blues",
        aspect="auto",
        title="Intensité des co-occurrences"
    )
    fig.update_layout(height=600)
    st.plotly_chart(fig, width='stretch')

    st.divider()

    # ── Graphe réseau ──────────────────────────────────────────────────────────
    st.subheader("Graphe de réseau — Top 20 paires")

    df_top = df.head(20)
    max_val = df_top["total"].max()

    fig2 = go.Figure()

    for _, row in df_top.iterrows():
        fig2.add_trace(go.Scatter(
            x=[row["skill_a"], row["skill_b"]],
            y=[0, 0],
            mode="lines",
            line=dict(
                width=row["total"] / max_val * 10,
                color="rgba(99, 110, 250, 0.4)"
            ),
            showlegend=False
        ))

    skills_in_top = list(set(
        df_top["skill_a"].tolist() + df_top["skill_b"].tolist()
    ))

    skill_counts = {}
    for _, row in df_top.iterrows():
        skill_counts[row["skill_a"]] = skill_counts.get(row["skill_a"], 0) + row["total"]
        skill_counts[row["skill_b"]] = skill_counts.get(row["skill_b"], 0) + row["total"]

    import math
    n = len(skills_in_top)
    positions = {
        skill: (math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n))
        for i, skill in enumerate(skills_in_top)
    }

    fig3 = go.Figure()

    for _, row in df_top.iterrows():
        x0, y0 = positions[row["skill_a"]]
        x1, y1 = positions[row["skill_b"]]
        fig3.add_trace(go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode="lines",
            line=dict(
                width=row["total"] / max_val * 8,
                color="rgba(99, 110, 250, 0.3)"
            ),
            showlegend=False,
            hoverinfo="none"
        ))

    fig3.add_trace(go.Scatter(
        x=[positions[s][0] for s in skills_in_top],
        y=[positions[s][1] for s in skills_in_top],
        mode="markers+text",
        text=skills_in_top,
        textposition="top center",
        marker=dict(
            size=[skill_counts.get(s, 1) / max_val * 40 + 10 for s in skills_in_top],
            color="rgb(99, 110, 250)",
            line=dict(width=2, color="white")
        ),
        showlegend=False
    ))

    fig3.update_layout(
        height=600,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="white"
    )
    st.plotly_chart(fig3, width='stretch')

    # ── Tableau brut ───────────────────────────────────────────────────────────
    with st.expander("Voir les données brutes"):
        st.dataframe(df, width='stretch')
