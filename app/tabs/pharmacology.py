"""
Pharmacology Tab - Mechanism, targets, and chemical structure
"""

import streamlit as st


def render(drug_name: str):
    """
    Render pharmacology tab.

    Args:
        drug_name: Name of selected drug
    """

    st.subheader("Mechanism of Action")

    st.markdown("""
    **Placeholder mechanism description:**

    Metformin decreases hepatic glucose production, decreases intestinal absorption of glucose,
    and improves insulin sensitivity by increasing peripheral glucose uptake and utilization.
    """)

    st.markdown("---")

    st.subheader("Molecular Structure")

    # TODO: Add RDKit 2D structure
    # TODO: Add 3D molecule viewer (STmol or py3Dmol)

    st.info("💡 Chemical structure visualization will be added with RDKit integration.")

    st.markdown("---")

    st.subheader("Target Receptors")

    # Placeholder target data
    target_data = [
        {"Target": "AMPK", "Affinity": "100 nM", "Interaction": "Activator"},
        {"Target": "Complex I", "Affinity": "50 uM", "Interaction": "Inhibitor"},
        {"Target": "GPR40", "Affinity": "200 nM", "Interaction": "Modulator"},
    ]

    st.table(target_data)

    st.info("💡 Target data will be fetched from ChEMBL via Supabase agent.")
