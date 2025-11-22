"""
Overview Tab - Drug scores and summary
"""

import streamlit as st
import plotly.graph_objects as go


def render(drug_name: str):
    """
    Render overview tab with drug scores and summary.

    Args:
        drug_name: Name of selected drug
    """

    st.subheader("Drug Scores Summary")

    # Placeholder scores (will come from Supabase agent)
    scores = {
        "Trial Progress": 85,
        "Mechanism": 72,
        "Safety": 68,
        "Evidence": 90,
        "Sentiment": 75
    }

    # Metric cards in columns
    cols = st.columns(5)

    for i, (score_name, score_value) in enumerate(scores.items()):
        with cols[i]:
            st.metric(
                label=score_name,
                value=f"{score_value}/100",
                delta=None  # TODO: Add comparison
            )

    st.markdown("---")

    # Radar chart
    st.subheader("Score Visualization")

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=list(scores.values()),
        theta=list(scores.keys()),
        fill='toself',
        name=drug_name
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False,
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Drug info section
    st.subheader("Drug Information")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Status:** Approved")
        st.markdown("**Class:** Antidiabetic")
        st.markdown("**First Approved:** 1995")

    with col2:
        st.markdown("**DrugBank ID:** DB00331")
        st.markdown("**ChEMBL ID:** CHEMBL1431")
        st.markdown("**Targets:** 5 known targets")

    # Placeholder notice
    st.info("💡 This is placeholder data. Real data will be fetched from Supabase.")
