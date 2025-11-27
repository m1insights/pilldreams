import streamlit as st
import requests
import pandas as pd

# Configuration
FASTAPI_URL = "http://localhost:8000"

st.set_page_config(page_title="Drug Intelligence Platform", layout="wide")
st.title("Biopharma Drug Intelligence Platform")

# Sidebar for actions
with st.sidebar:
    st.header("Filters")
    # Moved filters to sidebar for better layout
    gold_set_only = st.checkbox("Show Gold Set Only", value=False)

# Main Content
tab1, tab2 = st.tabs(["Gold Set Explorer", "Pipeline Explorer"])

with tab1:
    st.header("Gold Set Drugs (Approved/Phase 3)")
    
    # Fetch drugs
    try:
        params = {"gold_set_only": str(gold_set_only).lower()}
        response = requests.get(f"{FASTAPI_URL}/drugs", params=params)
        if response.status_code == 200:
            drugs = response.json()
            
            if not drugs:
                st.info("No drugs found. Run the ETL pipeline to populate data.")
            else:
                # Convert to DataFrame for easier display
                df = pd.DataFrame(drugs)
                
                # Display metrics
                st.metric("Total Drugs", len(df))
                if "is_gold_set" in df.columns:
                    st.metric("Gold Set Drugs", len(df[df["is_gold_set"] == True]))
                
                # Display table
                st.dataframe(
                    df[[
                        "name", "drug_type", "max_phase", 
                        "pubmed_count", "openfda_ae_count", "serious_ae_ratio", "is_gold_set"
                    ]],
                    use_container_width=True
                )
                
                # Detailed view
                st.subheader("Drug Details")
                selected_drug_name = st.selectbox("Select a drug to view details", df["name"].tolist())
                
                if selected_drug_name:
                    drug_data = df[df["name"] == selected_drug_name].iloc[0]
                    
                    st.markdown(f"### {drug_data['name']}")
                    st.write(f"**Type:** {drug_data['drug_type']}")
                    st.write(f"**Max Phase:** {drug_data['max_phase']}")
                    st.write(f"**PubMed Count:** {drug_data['pubmed_count']}")
                    st.write(f"**OpenFDA AE Count:** {drug_data['openfda_ae_count']}")
                    st.write(f"**Serious AE Ratio:** {drug_data['serious_ae_ratio']:.2f}")
                    
                    # Fetch targets
                    targets_response = requests.get(f"{FASTAPI_URL}/drugs/{drug_data['id']}/targets")
                    if targets_response.status_code == 200:
                        targets = targets_response.json()
                        if targets:
                            st.write("**Targets:**")
                            for t in targets:
                                st.write(f"- **{t['approved_symbol']}**: {t['mechanism_of_action']}")
                        else:
                            st.info("No targets found.")
                    
        else:
            st.error(f"Failed to fetch drugs: {response.text}")

    except Exception as e:
        st.error(f"Error connecting to backend: {e}. Make sure FastAPI is running.")

with tab2:
    st.header("Pipeline Assets (Phase 1-2)")
    st.info("These are experimental assets scored against the Gold Set.")
    
    try:
        response = requests.get(f"{FASTAPI_URL}/pipeline-assets")
        if response.status_code == 200:
            assets = response.json()
            
            if not assets:
                st.info("No pipeline assets found. Run the ETL pipeline.")
            else:
                df_assets = pd.DataFrame(assets)
                
                # Metrics
                st.metric("Total Pipeline Assets", len(df_assets))
                
                # Display table with Score
                st.dataframe(
                    df_assets[[
                        "name", "phase", "total_score", "bio_score", "chem_score", "tractability_score"
                    ]].sort_values("total_score", ascending=False),
                    use_container_width=True
                )
                
                # Detail View
                st.subheader("Asset Details")
                selected_asset = st.selectbox("Select an asset", df_assets["name"].tolist())
                
                if selected_asset:
                    asset_data = df_assets[df_assets["name"] == selected_asset].iloc[0]
                    
                    st.markdown(f"### {asset_data['name']}")
                    st.write(f"**Phase:** {asset_data['phase']}")
                    
                    # Score Breakdown
                    st.markdown("#### Scoring Analysis")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Score", f"{asset_data['total_score']:.1f}" if pd.notnull(asset_data['total_score']) else "N/A")
                    with col2:
                        st.metric("Bio Score", f"{asset_data['bio_score']:.1f}" if pd.notnull(asset_data['bio_score']) else "N/A")
                    with col3:
                        st.metric("Chem Score", f"{asset_data['chem_score']:.1f}" if pd.notnull(asset_data['chem_score']) else "N/A")
                    with col4:
                        st.metric("Tract Score", f"{asset_data['tractability_score']:.1f}" if pd.notnull(asset_data['tractability_score']) else "N/A")
                    
                    # Fetch targets
                    targets_response = requests.get(f"{FASTAPI_URL}/pipeline-assets/{asset_data['id']}/targets")
                    if targets_response.status_code == 200:
                        targets = targets_response.json()
                        if targets:
                            st.write("**Targets:**")
                            for t in targets:
                                st.write(f"- **{t['approved_symbol']}**: {t['mechanism_of_action']}")
    except Exception as e:
        st.error(f"Error fetching pipeline assets: {e}")
