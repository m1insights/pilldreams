"""
Trials & Evidence Tab - Clinical trials and evidence summary
"""

import streamlit as st
import pandas as pd


def render(drug_name: str):
    """
    Render trials & evidence tab.

    Args:
        drug_name: Name of selected drug
    """

    st.subheader("Clinical Trials Overview")

    # Placeholder trial stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Trials", "1,247")
    with col2:
        st.metric("Active Trials", "89")
    with col3:
        st.metric("Completed", "1,098")
    with col4:
        st.metric("Avg Enrollment", "324")

    st.markdown("---")

    st.subheader("Trial Timeline")

    # TODO: Add Plotly timeline visualization

    st.info("💡 Trial timeline visualization will be added.")

    st.markdown("---")

    st.subheader("Recent Trials")

    # Placeholder trial data
    trial_data = pd.DataFrame({
        "NCT ID": ["NCT04567890", "NCT04123456", "NCT03987654"],
        "Phase": ["III", "II", "III"],
        "Status": ["Recruiting", "Active", "Completed"],
        "Condition": ["Type 2 Diabetes", "PCOS", "Prediabetes"],
        "Enrollment": [500, 200, 1000],
        "Start Date": ["2023-01-15", "2022-06-01", "2021-03-10"]
    })

    st.dataframe(trial_data, use_container_width=True)

    st.markdown("---")

    st.subheader("Evidence Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("RCTs", "234")
    with col2:
        st.metric("Meta-Analyses", "45")
    with col3:
        st.metric("Median Pub Year", "2019")

    st.info("💡 Trial and evidence data will be fetched from ClinicalTrials.gov and PubMed.")
