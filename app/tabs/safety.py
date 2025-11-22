"""
Safety & Sentiment Tab - Adverse events and real-world sentiment
"""

import streamlit as st
import pandas as pd
import plotly.express as px


def render(drug_name: str):
    """
    Render safety & sentiment tab.

    Args:
        drug_name: Name of selected drug
    """

    st.subheader("Adverse Events (FDA OpenFDA)")

    # Placeholder adverse event data
    ae_data = pd.DataFrame({
        "MedDRA Term": ["Nausea", "Diarrhea", "Abdominal Pain", "Headache", "Dizziness"],
        "Case Count": [1234, 987, 654, 432, 321],
        "Serious": ["No", "No", "Yes", "No", "No"],
        "PRR": [1.2, 1.5, 2.1, 0.9, 1.1]
    })

    st.dataframe(ae_data, use_container_width=True)

    # Bar chart
    fig = px.bar(
        ae_data.head(10),
        x="MedDRA Term",
        y="Case Count",
        color="Serious",
        title="Top Adverse Events"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader("Real-World Sentiment (Reddit)")

    # Placeholder sentiment data
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Overall Sentiment", "0.68", delta="Positive")
    with col2:
        st.metric("Posts Analyzed", "1,234")
    with col3:
        st.metric("Subreddits", "5")

    st.markdown("**Sentiment by Dimension:**")

    sentiment_dims = pd.DataFrame({
        "Dimension": ["Mood", "Anxiety", "Weight", "Sexual", "Sleep"],
        "Sentiment": [0.72, -0.15, -0.45, -0.32, 0.55]
    })

    fig2 = px.bar(
        sentiment_dims,
        x="Dimension",
        y="Sentiment",
        color="Sentiment",
        color_continuous_scale="RdYlGn",
        title="Sentiment Analysis by Dimension"
    )

    st.plotly_chart(fig2, use_container_width=True)

    st.info("💡 Safety and sentiment data will be fetched from OpenFDA and Reddit.")
