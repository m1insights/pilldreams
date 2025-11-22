"""
pilldreams - Drug Intelligence Platform
Main Streamlit Application

Design inspired by Linear - minimal, black & white, clean
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.supabase_client import get_client

# Page config
st.set_page_config(
    page_title="pilldreams | Drug Intelligence",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS - Linear-inspired black & white design
st.markdown("""
<style>
    /* Global dark theme */
    :root {
        --bg-primary: #0A0A0A;
        --bg-secondary: #111111;
        --bg-tertiary: #1A1A1A;
        --border-color: #2A2A2A;
        --text-primary: #E5E5E5;
        --text-secondary: #A0A0A0;
        --text-muted: #6B6B6B;
        --accent: #FFFFFF;
        --hover-bg: #1F1F1F;
    }

    /* Main background */
    .stApp {
        background-color: var(--bg-primary);
        color: var(--text-primary);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Custom header */
    .main-header {
        font-size: 2.5rem;
        font-weight: 600;
        letter-spacing: -0.02em;
        color: var(--accent);
        margin-bottom: 0.5rem;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    .subtitle {
        font-size: 1rem;
        color: var(--text-secondary);
        margin-bottom: 3rem;
        font-weight: 400;
    }

    /* Search bar */
    .stTextInput > div > div > input {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-color);
        color: var(--text-primary);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-size: 0.95rem;
        transition: all 0.2s ease;
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--accent);
        box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.1);
    }

    .stTextInput > div > div > input::placeholder {
        color: var(--text-muted);
    }

    /* Select box */
    .stSelectbox > div > div {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-color);
        color: var(--text-primary);
        border-radius: 8px;
    }

    /* Cards */
    .drug-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.2s ease;
    }

    .drug-card:hover {
        background: var(--hover-bg);
        border-color: var(--text-muted);
    }

    .drug-name {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--accent);
        margin-bottom: 0.5rem;
    }

    .drug-meta {
        font-size: 0.875rem;
        color: var(--text-secondary);
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .badge-phase {
        background: rgba(255, 255, 255, 0.1);
        color: var(--accent);
        border: 1px solid var(--border-color);
    }

    .badge-status {
        background: rgba(59, 130, 246, 0.1);
        color: #60A5FA;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }

    .badge-sponsor {
        background: rgba(168, 85, 247, 0.1);
        color: #C084FC;
        border: 1px solid rgba(168, 85, 247, 0.2);
    }

    /* Metrics */
    .metric-container {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 600;
        color: var(--accent);
        margin-bottom: 0.25rem;
    }

    .metric-label {
        font-size: 0.875rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Tables */
    .dataframe {
        background-color: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
    }

    .dataframe th {
        background-color: var(--bg-tertiary) !important;
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        font-size: 0.75rem !important;
        letter-spacing: 0.05em !important;
        border-bottom: 1px solid var(--border-color) !important;
    }

    .dataframe td {
        border-bottom: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: var(--accent);
        color: var(--bg-primary);
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background-color: var(--text-primary);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(255, 255, 255, 0.1);
    }

    /* Divider */
    hr {
        border: none;
        border-top: 1px solid var(--border-color);
        margin: 2rem 0;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }

    .streamlit-expanderContent {
        background-color: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-top: none !important;
    }

    /* Info boxes */
    .stInfo {
        background-color: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-secondary) !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database connection
@st.cache_resource
def init_db():
    return get_client()

db = init_db()

# Initialize session state
if 'selected_drug' not in st.session_state:
    st.session_state.selected_drug = None

# Header
st.markdown('<div class="main-header">💊 pilldreams</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Drug intelligence for investors. Real-time pipeline analysis.</div>', unsafe_allow_html=True)

# =======================
# DRUG DETAIL VIEW
# =======================
if st.session_state.selected_drug:
    # Back button
    if st.button("← Back to Search"):
        st.session_state.selected_drug = None
        st.rerun()

    st.markdown("---")

    # Fetch drug data
    drug_id = st.session_state.selected_drug
    drug_response = db.client.table('drug').select('*').eq('id', drug_id).execute()

    if not drug_response.data:
        st.error("Drug not found")
        st.session_state.selected_drug = None
        st.rerun()

    drug = drug_response.data[0]

    # Drug header
    st.markdown(f'<div class="main-header">{drug["name"]}</div>', unsafe_allow_html=True)

    # Get trials for this drug
    interventions = db.client.table('trial_intervention').select('trial_id').eq('drug_id', drug_id).execute()
    trial_ids = [i['trial_id'] for i in interventions.data] if interventions.data else []

    if trial_ids:
        trials_response = db.client.table('trial').select('*').in_('nct_id', trial_ids).execute()
        trials = trials_response.data
    else:
        trials = []

    # Get targets/bindings from ChEMBL
    bindings_response = db.client.table('drugtarget').select('*, target(*)').eq('drug_id', drug_id).execute()
    bindings = bindings_response.data

    # Get safety data
    safety_response = db.client.table('safetyaggregate').select('*').eq('drug_id', drug_id).order('case_count', desc=True).limit(20).execute()
    safety_events = safety_response.data

    # Get evidence data
    evidence_response = db.client.table('evidenceaggregate').select('*').eq('drug_id', drug_id).execute()
    evidence = evidence_response.data[0] if evidence_response.data else None

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🧬 Pharmacology", "🔬 Trials & Evidence", "⚠️ Safety"])

    # ==================
    # TAB 1: OVERVIEW
    # ==================
    with tab1:
        st.markdown("### Key Metrics")
        st.markdown("")

        # Metrics row
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

        with metric_col1:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value">{len(trials)}</div>
                <div class="metric-label">Total Trials</div>
            </div>
            """, unsafe_allow_html=True)

        with metric_col2:
            active_trial_count = len([t for t in trials if t['status'] in ['RECRUITING', 'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION']])
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value">{active_trial_count}</div>
                <div class="metric-label">Active Trials</div>
            </div>
            """, unsafe_allow_html=True)

        with metric_col3:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value">{len(bindings)}</div>
                <div class="metric-label">Known Targets</div>
            </div>
            """, unsafe_allow_html=True)

        with metric_col4:
            n_rcts = evidence['n_rcts'] if evidence else 0
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value">{n_rcts}</div>
                <div class="metric-label">RCTs Published</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")
        st.markdown("---")

        # Trial phase distribution
        if trials:
            st.markdown("### Trial Phase Distribution")
            phase_counts = {}
            for trial in trials:
                phase = trial['phase'] or 'Unknown'
                phase_counts[phase] = phase_counts.get(phase, 0) + 1

            phase_df = pd.DataFrame([
                {"Phase": phase, "Count": count}
                for phase, count in sorted(phase_counts.items())
            ])

            st.dataframe(phase_df, use_container_width=True, hide_index=True)

    # ==================
    # TAB 2: PHARMACOLOGY
    # ==================
    with tab2:
        st.markdown("### Drug Targets & Binding Affinity")
        st.markdown("")

        if bindings:
            # Build targets dataframe
            targets_data = []
            for binding in bindings:
                target = binding.get('target', {})
                targets_data.append({
                    "Target": target.get('name', 'Unknown'),
                    "Symbol": target.get('symbol', 'N/A'),
                    "Type": target.get('target_type', 'Unknown'),
                    "Affinity": f"{binding.get('affinity_value', 'N/A')} nM" if binding.get('affinity_value') else "N/A",
                    "Affinity Type": binding.get('affinity_type', 'N/A'),
                    "Measurements": binding.get('measurement_count', 'N/A')
                })

            targets_df = pd.DataFrame(targets_data)
            st.dataframe(targets_df, use_container_width=True, hide_index=True)
        else:
            st.info("No target binding data available yet. ChEMBL ingestion may still be running.")

        if drug.get('chembl_id'):
            st.markdown(f"**ChEMBL ID:** {drug['chembl_id']}")

    # ==================
    # TAB 3: TRIALS & EVIDENCE
    # ==================
    with tab3:
        # Evidence summary
        if evidence:
            st.markdown("### Evidence Summary")
            st.markdown("")

            ev_col1, ev_col2, ev_col3 = st.columns(3)

            with ev_col1:
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value">{evidence['n_rcts']}</div>
                    <div class="metric-label">RCTs</div>
                </div>
                """, unsafe_allow_html=True)

            with ev_col2:
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value">{evidence['n_meta_analyses']}</div>
                    <div class="metric-label">Meta-Analyses</div>
                </div>
                """, unsafe_allow_html=True)

            with ev_col3:
                median_year = evidence.get('median_pub_year', 'N/A')
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value">{median_year}</div>
                    <div class="metric-label">Median Pub Year</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("")
            st.markdown("---")

        # Clinical trials table
        st.markdown("### Clinical Trials")
        st.markdown("")

        if trials:
            trials_data = []
            for trial in trials:
                trials_data.append({
                    "NCT ID": trial.get('nct_id', 'N/A'),
                    "Phase": trial.get('phase', 'Unknown'),
                    "Status": trial.get('status', 'Unknown'),
                    "Condition": trial.get('condition', 'N/A')[:50] + "..." if len(trial.get('condition', '')) > 50 else trial.get('condition', 'N/A'),
                    "Enrollment": trial.get('enrollment', 'N/A'),
                    "Start Date": trial.get('start_date', 'N/A')
                })

            trials_df = pd.DataFrame(trials_data)
            st.dataframe(trials_df, use_container_width=True, hide_index=True)
        else:
            st.info("No clinical trial data available.")

    # ==================
    # TAB 4: SAFETY
    # ==================
    with tab4:
        st.markdown("### Adverse Events (OpenFDA)")
        st.markdown("")

        if safety_events:
            safety_data = []
            for event in safety_events:
                safety_data.append({
                    "Adverse Event": event.get('meddra_term', 'Unknown'),
                    "Case Count": event.get('case_count', 0),
                    "Serious": "Yes" if event.get('is_serious') else "No",
                    "PRR Score": f"{event.get('disproportionality_metric', 0):.2f}" if event.get('disproportionality_metric') else "N/A"
                })

            safety_df = pd.DataFrame(safety_data)
            st.dataframe(safety_df, use_container_width=True, hide_index=True)

            st.markdown("")
            st.info("⚠️ **Note:** Adverse event data is derived from FDA reports and does not imply causation. Always consult professional medical guidance.")
        else:
            st.info("No adverse event data available yet. OpenFDA ingestion may still be running.")

    # Stop execution here - don't show search view
    st.stop()

# =======================
# SEARCH VIEW (default)
# =======================

# Search / Filter Section
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    search_query = st.text_input(
        "Search compounds",
        placeholder="Enter drug name (e.g., Atezolizumab, psilocybin, metformin...)",
        label_visibility="collapsed"
    )

with col2:
    phase_filter = st.selectbox(
        "Phase",
        options=["All Phases", "1", "2", "3"],
        label_visibility="collapsed"
    )

with col3:
    status_filter = st.selectbox(
        "Status",
        options=["All Statuses", "RECRUITING", "ACTIVE_NOT_RECRUITING", "ENROLLING_BY_INVITATION"],
        label_visibility="collapsed"
    )

st.markdown("---")

# Metrics Row
metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

# Fetch metrics
total_drugs = db.client.table('drug').select('*', count='exact').limit(0).execute().count
total_trials = db.client.table('trial').select('*', count='exact').limit(0).execute().count

# Calculate active trials
active_trials = db.client.table('trial').select('*', count='exact').in_('status', [
    'RECRUITING', 'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION', 'NOT_YET_RECRUITING'
]).limit(0).execute().count

# Phase 3 trials
phase3_trials = db.client.table('trial').select('*', count='exact').eq('phase', '3').limit(0).execute().count

with metric_col1:
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-value">{total_drugs:,}</div>
        <div class="metric-label">Pipeline Compounds</div>
    </div>
    """, unsafe_allow_html=True)

with metric_col2:
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-value">{total_trials:,}</div>
        <div class="metric-label">Total Trials</div>
    </div>
    """, unsafe_allow_html=True)

with metric_col3:
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-value">{active_trials:,}</div>
        <div class="metric-label">Active Trials</div>
    </div>
    """, unsafe_allow_html=True)

with metric_col4:
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-value">{phase3_trials:,}</div>
        <div class="metric-label">Phase 3 Trials</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Query drugs with trials
if search_query:
    # Search for drugs matching query
    drugs_response = db.client.table('drug').select('*').ilike('name', f'%{search_query}%').limit(20).execute()
    drugs = drugs_response.data
else:
    # Show recent drugs
    drugs_response = db.client.table('drug').select('*').order('created_at', desc=True).limit(20).execute()
    drugs = drugs_response.data

# Display results
if drugs:
    st.markdown(f"### {len(drugs)} Compounds Found")
    st.markdown("")

    for drug in drugs:
        # Get trials for this drug via junction table (many-to-many)
        # First, get trial IDs from junction table
        interventions = db.client.table('trial_intervention').select('trial_id').eq('drug_id', drug['id']).execute()
        trial_ids = [i['trial_id'] for i in interventions.data] if interventions.data else []

        # Then fetch full trial data
        if trial_ids:
            trials_response = db.client.table('trial').select('*').in_('nct_id', trial_ids).execute()
            trials = trials_response.data
        else:
            trials = []

        # Build drug card
        trial_count = len(trials)

        # Create clickable button to view drug details
        col_btn, col_info = st.columns([3, 1])
        with col_btn:
            if st.button(f"**{drug['name']}** — {trial_count} trials", key=f"drug_{drug['id']}", use_container_width=True):
                st.session_state.selected_drug = drug['id']
                st.rerun()

        with col_info:
            phases = list(set([t['phase'] for t in trials if t['phase']]))
            if phases:
                st.markdown(f"<span class='badge badge-phase'>Phase {', '.join(sorted(phases))}</span>", unsafe_allow_html=True)
else:
    st.info("No compounds found. Try a different search term.")

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: var(--text-muted); font-size: 0.875rem; padding: 2rem 0;">
    pilldreams © 2025 — Drug intelligence for serious investors
</div>
""", unsafe_allow_html=True)
