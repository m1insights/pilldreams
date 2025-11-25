"""
pilldreams - Drug Intelligence Platform
Main Streamlit Application

Design inspired by Linear - minimal, black & white, clean
"""

import streamlit as st
import streamlit_shadcn_ui as ui
import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.supabase_client import get_client
from core.trial_design_scorer import get_quality_category
from core.competitor_analysis import get_full_competitive_landscape
from core.fda_precedent import calculate_approval_probability
from core.auth import require_authentication
from core.scoring import DrugScorer
from core.drug_display_utils import get_unique_drugs, format_variant_info, should_show_variant_info

# Page config
st.set_page_config(
    page_title="pilldreams | Drug Intelligence",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# AUTHENTICATION CHECK - Must be authenticated to access app
user = require_authentication()

# Load professional custom CSS
css_path = Path(__file__).parent / 'styles' / 'custom.css'
with open(css_path) as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Inject Material Icons for shadcn components
st.markdown('<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">', unsafe_allow_html=True)

# Initialize database connection
@st.cache_resource
def init_db():
    return get_client()

db = init_db()

def render_affinity_spectrum(bindings):
    """
    Renders a 'Potency Spectrum' visualization for drug targets.
    Visualizes affinity (nM) on a log scale as 'Signal Intensity'.
    """
    if not bindings:
        st.info("No target binding data available.")
        return

    st.markdown('<div style="margin-bottom: 1rem; font-family: var(--font-mono); color: var(--text-secondary);">SIGNAL INTENSITY (LOG SCALE)</div>', unsafe_allow_html=True)

    for binding in bindings:
        target = binding.get('target', {})
        symbol = target.get('symbol', 'UNKNOWN')
        name = target.get('name', 'Unknown Target')
        affinity_val = binding.get('affinity_value')
        
        # Calculate 'intensity' (0-100%) based on affinity
        # Lower nM = Higher Potency. 
        # Scale: 0.1nM (100%) to 10,000nM (0%)
        if affinity_val:
            try:
                val = float(affinity_val)
                # Log scale normalization roughly: -log10(val) scaled
                # Let's do a simple heuristic for visual impact
                if val <= 0.1: intensity = 100
                elif val >= 10000: intensity = 5
                else:
                    # Log scale interpolation between 0.1 (100%) and 10000 (5%)
                    # log(0.1) = -1, log(10000) = 4. Range = 5 orders of magnitude.
                    import math
                    log_val = math.log10(val)
                    # Map -1 -> 100, 4 -> 5
                    # y = mx + c
                    # 100 = m(-1) + c
                    # 5 = m(4) + c
                    # 95 = -5m => m = -19
                    # 100 = 19 + c => c = 81
                    intensity = -19 * log_val + 81
                    intensity = max(5, min(100, intensity))
            except:
                intensity = 10
        else:
            intensity = 0
            
        st.markdown(f"""
        <div class="affinity-bar-container">
            <div class="affinity-label" title="{name}">{symbol}</div>
            <div class="affinity-track">
                <div class="affinity-fill" style="width: {intensity}%;"></div>
            </div>
            <div class="affinity-value">{affinity_val} nM</div>
        </div>
        """, unsafe_allow_html=True)

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
    # Back button (shadcn)
    # Back button
    if st.button("← Back to Search", key="back_btn"):
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

    # Pre-fetch approval data for hero section
    try:
        hero_approval_data = calculate_approval_probability(drug_id)
        is_approved = hero_approval_data.get('is_approved', False)
        approval_prob = hero_approval_data.get('approval_probability', 0)
    except:
        is_approved = drug.get('is_approved', False)
        approval_prob = 0

    # Determine status chips and gauge display
    if is_approved:
        status_chip = '<span class="signal-chip signal-bullish">✓ FDA APPROVED</span>'
        gauge_value = "APPROVED"
        gauge_label = "Status"
    else:
        status_chip = '<span class="signal-chip signal-neutral">IN DEVELOPMENT</span>'
        gauge_value = f"{approval_prob * 100:.0f}%" if approval_prob > 0 else "—"
        gauge_label = "Approval Prob."

    # Drug header (Hero Section)
    st.markdown(f"""
    <div class="hero-container">
        <div>
            <div class="hero-title">{drug["name"]}</div>
            <div class="hero-subtitle">{drug.get('mechanism_of_action', 'Mechanism Undefined')}</div>
            <div style="margin-top: 1rem;">
                {status_chip}
            </div>
        </div>
        <div class="gauge-container">
             <div style="text-align: center;">
                <div class="gauge-value">{gauge_value}</div>
                <div class="gauge-label">{gauge_label}</div>
             </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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

        # Metrics row with shadcn metric_card components
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

        # Drug Intelligence Scores
        st.markdown("### Drug Intelligence Scores")
        st.markdown("")

        try:
            scorer = DrugScorer()
            scores = scorer.calculate_all_scores(drug_id)

            score_col1, score_col2, score_col3, score_col4 = st.columns(4)

            with score_col1:
                score_val = scores['trial_progress_score']
                if score_val >= 70:
                    badge_class = "badge-quality-excellent"
                elif score_val >= 50:
                    badge_class = "badge-quality-good"
                elif score_val >= 30:
                    badge_class = "badge-quality-fair"
                else:
                    badge_class = "badge-quality-poor"

                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value">{score_val}</div>
                    <div class="metric-label">Trial Progress</div>
                    <div class="badge {badge_class}" style="margin-top: 0.5rem;">
                        /100
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with score_col2:
                score_val = scores['mechanism_score']
                if score_val >= 70:
                    badge_class = "badge-quality-excellent"
                elif score_val >= 50:
                    badge_class = "badge-quality-good"
                elif score_val >= 30:
                    badge_class = "badge-quality-fair"
                else:
                    badge_class = "badge-quality-poor"

                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value">{score_val}</div>
                    <div class="metric-label">Mechanism Quality</div>
                    <div class="badge {badge_class}" style="margin-top: 0.5rem;">
                        /100
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with score_col3:
                score_val = scores['safety_score']
                if score_val >= 70:
                    badge_class = "badge-quality-excellent"
                elif score_val >= 50:
                    badge_class = "badge-quality-good"
                elif score_val >= 30:
                    badge_class = "badge-quality-fair"
                else:
                    badge_class = "badge-quality-poor"

                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value">{score_val}</div>
                    <div class="metric-label">Safety Profile</div>
                    <div class="badge {badge_class}" style="margin-top: 0.5rem;">
                        /100
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with score_col4:
                score_val = scores['overall_score']
                if score_val >= 70:
                    badge_class = "badge-quality-excellent"
                elif score_val >= 50:
                    badge_class = "badge-quality-good"
                elif score_val >= 30:
                    badge_class = "badge-quality-fair"
                else:
                    badge_class = "badge-quality-poor"

                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value">{score_val}</div>
                    <div class="metric-label">Overall Score</div>
                    <div class="badge {badge_class}" style="margin-top: 0.5rem;">
                        Composite
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Score explanation
            with st.expander("📊 How are these scores calculated?"):
                st.markdown(f"""
                **Trial Progress Score ({scores['trial_progress_score']}/100)**
                - Highest phase reached (0-40 pts)
                - Trial completion rate (0-20 pts)
                - Sponsor quality (0-15 pts)
                - Trial design quality (0-15 pts)
                - Enrollment size (0-10 pts)

                **Mechanism Score ({scores['mechanism_score']}/100)**
                - Target validation (0-30 pts)
                - Selectivity (0-30 pts)
                - Binding affinity (0-25 pts)
                - Measurement count (0-15 pts)

                **Safety Score ({scores['safety_score']}/100)**
                - Serious adverse events penalty (0-40 pts)
                - Total adverse event count penalty (0-30 pts)
                - Disproportionality signals penalty (0-30 pts)
                - Higher score = better safety profile

                **Overall Score ({scores['overall_score']}/100)**
                - Weighted average: 40% trial + 30% mechanism + 30% safety
                """)

        except Exception as e:
            st.info(f"Drug intelligence scores unavailable: {str(e)}")

        st.markdown("")
        st.markdown("---")

        # FDA Approval Status / Probability
        try:
            approval_data = calculate_approval_probability(drug_id)

            # Check if drug is already approved
            if approval_data.get('is_approved'):
                st.markdown("### FDA Approval Status")
                st.markdown("")

                approval_col1, approval_col2 = st.columns(2)

                with approval_col1:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-value" style="color: var(--neon-green);">✓ APPROVED</div>
                        <div class="metric-label">FDA Status</div>
                        <div class="badge badge-quality-excellent" style="margin-top: 0.5rem;">
                            {approval_data['confidence']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with approval_col2:
                    approval_date = approval_data.get('first_approval_date', 'Unknown')
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-value">{approval_date or 'On Record'}</div>
                        <div class="metric-label">First Approved</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("")

                if approval_data.get('reason'):
                    st.info(f"ℹ️ {approval_data['reason']}")

            # Pipeline drug - show approval probability
            elif approval_data.get('current_phase'):
                st.markdown("### FDA Approval Probability")
                st.markdown("")

                prob_pct = approval_data['approval_probability'] * 100

                # Color code based on probability
                if prob_pct >= 50:
                    prob_badge_class = "badge-quality-excellent"
                elif prob_pct >= 30:
                    prob_badge_class = "badge-quality-good"
                elif prob_pct >= 15:
                    prob_badge_class = "badge-quality-fair"
                else:
                    prob_badge_class = "badge-quality-poor"

                prob_col1, prob_col2, prob_col3 = st.columns(3)

                with prob_col1:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-value">{prob_pct:.1f}%</div>
                        <div class="metric-label">Approval Probability</div>
                        <div class="badge {prob_badge_class}" style="margin-top: 0.5rem;">
                            {approval_data['confidence']} Confidence
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with prob_col2:
                    base_pct = approval_data['base_success_rate'] * 100
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-value">{base_pct:.1f}%</div>
                        <div class="metric-label">Historical Rate</div>
                        <div class="badge badge-phase" style="margin-top: 0.5rem;">
                            Phase {approval_data['current_phase']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with prob_col3:
                    quality_adj_pct = approval_data['quality_adjustment'] * 100
                    comp_adj_pct = approval_data['competitive_adjustment'] * 100
                    total_adj_pct = quality_adj_pct + comp_adj_pct

                    if total_adj_pct > 0:
                        adj_badge = "badge-quality-good"
                        adj_sign = "+"
                    elif total_adj_pct < 0:
                        adj_badge = "badge-quality-poor"
                        adj_sign = ""
                    else:
                        adj_badge = "badge-phase"
                        adj_sign = ""

                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-value">{adj_sign}{total_adj_pct:+.1f}%</div>
                        <div class="metric-label">Adjustments</div>
                        <div class="badge {adj_badge}" style="margin-top: 0.5rem;">
                            Trial Quality + Competition
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("")

                # Explanation
                with st.expander("📊 How is this calculated?"):
                    st.markdown(f"""
                    **Base Success Rate**: {base_pct:.1f}%
                    - Historical Phase {approval_data['current_phase']} → Approval rate for {approval_data.get('indication', 'this indication')}
                    - Based on {approval_data.get('n_indication_trials', 'N/A')} trials in this indication

                    **Trial Quality Adjustment**: {quality_adj_pct:+.1f}%
                    - Excellent trial designs (+10%), Poor designs (-10%)

                    **Competitive Adjustment**: {comp_adj_pct:+.1f}%
                    - Strong market position (+5%), Challenging position (-5%)

                    **Final Probability**: {prob_pct:.1f}%
                    """)

            else:
                st.info("Insufficient trial data to calculate approval probability.")

        except Exception as e:
            st.info(f"Approval probability analysis unavailable: {str(e)}")

        st.markdown("")
        st.markdown("---")

        # Competitive Landscape
        st.markdown("### Competitive Landscape")
        st.markdown("")

        try:
            landscape = get_full_competitive_landscape(drug_id)
            advantage = landscape['competitive_advantage']

            # Competitive advantage score
            comp_col1, comp_col2, comp_col3 = st.columns(3)

            with comp_col1:
                score = advantage['score']
                category = advantage['category']

                # Color code based on score
                if score >= 80:
                    badge_class = "badge-quality-excellent"
                elif score >= 60:
                    badge_class = "badge-quality-good"
                elif score >= 40:
                    badge_class = "badge-quality-fair"
                else:
                    badge_class = "badge-quality-poor"

                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value">{score}</div>
                    <div class="metric-label">Competitive Advantage</div>
                    <div class="badge {badge_class}" style="margin-top: 0.5rem;">{category}</div>
                </div>
                """, unsafe_allow_html=True)

            with comp_col2:
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value">{advantage['indication_competitors']}</div>
                    <div class="metric-label">Indication Competitors</div>
                    <div class="badge badge-sponsor" style="margin-top: 0.5rem;">{advantage['market_position']}</div>
                </div>
                """, unsafe_allow_html=True)

            with comp_col3:
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value">{advantage['target_competitors']}</div>
                    <div class="metric-label">Target Competitors</div>
                    <div class="badge badge-phase" style="margin-top: 0.5rem;">{advantage['phase_leadership']}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("")

            # Show top competitors if any
            if landscape['indication_competitors']:
                with st.expander(f"📊 View Top Indication Competitors ({len(landscape['indication_competitors'])})"):
                    comp_data = []
                    for comp in landscape['indication_competitors'][:10]:
                        comp_data.append({
                            "Drug": comp.get('drug_name', 'Unknown'),
                            "Condition": comp.get('condition', 'N/A'),
                            "Highest Phase": comp.get('highest_phase', 'N/A'),
                            "Trials": comp.get('trial_count', 0)
                        })

                    if comp_data:
                        comp_df = pd.DataFrame(comp_data)
                        st.dataframe(comp_df, use_container_width=True, hide_index=True)

            if landscape['target_competitors']:
                with st.expander(f"🎯 View Drugs Sharing Targets ({len(landscape['target_competitors'])})"):
                    target_data = []
                    for comp in landscape['target_competitors'][:10]:
                        target_data.append({
                            "Drug": comp.get('drug_name', 'Unknown'),
                            "Target": comp.get('target_symbol', 'N/A'),
                            "Affinity": f"{comp.get('affinity_value', 'N/A')} nM" if comp.get('affinity_value') else "N/A"
                        })

                    if target_data:
                        target_df = pd.DataFrame(target_data)
                        st.dataframe(target_df, use_container_width=True, hide_index=True)

        except Exception as e:
            st.info(f"Competitive landscape analysis unavailable: {str(e)}")

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
        st.markdown("### Target Potency Spectrum")
        st.markdown("Binding affinity visualized as signal intensity (Log Scale).")
        st.markdown("")

        render_affinity_spectrum(bindings)

        if drug.get('chembl_id'):
            st.markdown("")
            st.markdown(f"**ChEMBL ID:** `{drug['chembl_id']}`")

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
            # Calculate trial quality distribution
            quality_dist = {"Excellent": 0, "Good": 0, "Fair": 0, "Poor": 0, "Unscored": 0}
            for trial in trials:
                score = trial.get('design_quality_score')
                if score is not None:
                    category = get_quality_category(score)
                    quality_dist[category] += 1
                else:
                    quality_dist["Unscored"] += 1

            # Show quality distribution summary
            if quality_dist["Excellent"] + quality_dist["Good"] + quality_dist["Fair"] + quality_dist["Poor"] > 0:
                st.markdown(f"""
                <div style="margin-bottom: 1rem; color: var(--text-secondary);">
                    <span class="badge badge-quality-excellent">{quality_dist['Excellent']} Excellent</span>
                    <span class="badge badge-quality-good">{quality_dist['Good']} Good</span>
                    <span class="badge badge-quality-fair">{quality_dist['Fair']} Fair</span>
                    <span class="badge badge-quality-poor">{quality_dist['Poor']} Poor</span>
                </div>
                """, unsafe_allow_html=True)

            # Render clickable trial cards
            for trial in trials:
                score = trial.get('design_quality_score')
                category = get_quality_category(score) if score is not None else "Unscored"
                
                if category == "Excellent":
                    badge_class = "badge-quality-excellent"
                elif category == "Good":
                    badge_class = "badge-quality-good"
                elif category == "Fair":
                    badge_class = "badge-quality-fair"
                else:
                    badge_class = "badge-quality-poor"

                quality_text = f"{score} - {category}" if score is not None else "Scoring..."
                
                # Card container
                with st.container():
                    col_trial_info, col_trial_action = st.columns([4, 1])
                    with col_trial_info:
                        st.markdown(f"""
                        <div style="padding: 12px; background: rgba(255,255,255,0.03); border-radius: 8px; border: 1px solid var(--border-glass); margin-bottom: 8px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                <span style="font-family: var(--font-mono); color: var(--neon-blue); font-size: 0.8rem;">{trial.get('nct_id')}</span>
                                <span class="badge {badge_class}">{quality_text}</span>
                            </div>
                            <div style="font-weight: 500; margin-bottom: 4px;">{trial.get('title', 'No Title')}</div>
                            <div style="font-size: 0.8rem; color: var(--text-secondary);">
                                {trial.get('phase', 'Unknown Phase')} • {trial.get('status', 'Unknown Status')} • {trial.get('enrollment', 'N/A')} Enrolled
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_trial_action:
                        if st.button("View Details", key=f"btn_trial_{trial['nct_id']}", use_container_width=True):
                            st.session_state.selected_trial = trial
                            st.rerun()
        else:
            st.info("No clinical trial data available.")
            
    # Check for selected trial to show modal/detail view
    if 'selected_trial' in st.session_state and st.session_state.selected_trial:
        trial = st.session_state.selected_trial
        
        @st.dialog("Trial Details", width="large")
        def show_trial_details():
            st.markdown(f"### {trial.get('title')}")
            st.markdown(f"**NCT ID:** `{trial.get('nct_id')}`")
            
            st.markdown("---")
            
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                st.markdown(f"**Phase:** {trial.get('phase')}")
                st.markdown(f"**Status:** {trial.get('status')}")
                st.markdown(f"**Start Date:** {trial.get('start_date')}")
            with col_t2:
                st.markdown(f"**Enrollment:** {trial.get('enrollment')}")
                st.markdown(f"**Conditions:** {trial.get('condition')}")
                st.markdown(f"**Sponsor:** {trial.get('sponsor')}")
                
            st.markdown("---")
            st.markdown("### Design Quality Analysis")
            st.json(trial.get('design_quality_reasoning', {}))
            
            if st.button("Close"):
                st.session_state.selected_trial = None
                st.rerun()
                
        show_trial_details()

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
    # Fetch all drug names for autocomplete
    all_drugs_response = db.client.table('drug').select('name').execute()
    drug_names = [d['name'] for d in all_drugs_response.data] if all_drugs_response.data else []
    
    search_query = st.selectbox(
        "Search compounds",
        options=drug_names,
        index=None,
        placeholder="Select a drug (e.g., Psilocybin, Metformin...)",
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

# Metrics Row with shadcn metric_card components
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
    # Search for drugs matching query (exact match from selectbox)
    drugs_response = db.client.table('drug').select('*').eq('name', search_query).execute()
    raw_drugs = drugs_response.data
else:
    # Show recent drugs
    drugs_response = db.client.table('drug').select('*').order('created_at', desc=True).limit(100).execute()
    raw_drugs = drugs_response.data

# Apply smart deduplication to collapse dosage variants
# Example: "Metformin 500mg", "Metformin 850mg" → single "Metformin" entry
drugs = get_unique_drugs(raw_drugs) if raw_drugs else []

# Limit to 20 unique drugs for display
drugs = drugs[:20]

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

        # Build drug card with shadcn components
        trial_count = len(trials)

        # Use normalized display_name for cleaner UI
        display_name = drug.get('display_name', drug['name'])

        # Show variant info if drug has multiple dosage forms
        variant_info = ""
        if should_show_variant_info(drug):
            variant_info = f" ({format_variant_info(drug.get('variant_count', 1))})"

        # Create clickable button to view drug details
        col_btn, col_info = st.columns([3, 1])
        with col_btn:
            if st.button(
                f"{display_name}{variant_info} — {trial_count} trials",
                key=f"drug_btn_{drug['id']}",
                use_container_width=True
            ):
                st.session_state.selected_drug = drug['id']
                st.rerun()

        with col_info:
            phases = list(set([t['phase'] for t in trials if t['phase']]))
            if phases:
                phase_text = ', '.join(sorted(phases))
                ui.badges(badge_list=[(f"Phase {phase_text}", "default")], key=f"badge_{drug['id']}")
else:
    st.info("No compounds found. Try a different search term.")

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: var(--text-muted); font-size: 0.875rem; padding: 2rem 0;">
    pilldreams © 2025 — Drug intelligence for serious investors
</div>
""", unsafe_allow_html=True)
