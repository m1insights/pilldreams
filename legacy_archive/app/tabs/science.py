
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.supabase_client import get_client

def render(company):
    """
    Render Science tab for a company.
    
    Args:
        company: Company dictionary from database
    """
    db = get_client()
    company_id = company['id']
    ticker = company['ticker']
    
    st.markdown(f"### {ticker} Scientific Intelligence")
    
    # 1. Fetch Drugs linked to Company
    # Join: Company -> CompanyDrug -> Drug
    drugs = db.client.table("company_drug").select("drug(id, name)").eq("company_id", company_id).execute().data
    
    if not drugs:
        st.info("No drugs found for this company.")
        return
        
    # Flatten list
    drug_list = [d['drug'] for d in drugs if d['drug']]
    
    # Create tabs for each drug
    if not drug_list:
        st.info("No drug details available.")
        return
        
    drug_names = [d['name'] for d in drug_list]
    drug_tabs = st.tabs(drug_names)
    
    for i, tab in enumerate(drug_tabs):
        drug = drug_list[i]
        with tab:
            # st.markdown(f"**Mechanism:** {drug.get('mechanism_of_action') or 'Unknown'}")
            
            # 2. Fetch Targets for this Drug
            # Join: Drug -> DrugTarget -> Target
            targets_response = db.client.table("drugtarget").select("target(id, name, uniprot_id, description)").eq("drug_id", drug['id']).execute()
            targets = [t['target'] for t in targets_response.data if t['target']]
            
            if not targets:
                st.info("No molecular targets identified.")
                continue
                
            st.markdown("#### Molecular Targets & Disease Associations")
            
            for target in targets:
                with st.expander(f"🎯 {target['name']}", expanded=True):
                    if target.get('description'):
                        st.caption(target['description'])
                    
                    # 3. Fetch Disease Associations (Open Targets)
                    associations = db.client.table("target_disease_association").select("*").eq("target_id", target['id']).order("association_score", desc=True).limit(10).execute().data
                    
                    if associations:
                        # Format for display
                        assoc_data = []
                        for a in associations:
                            score = a['association_score']
                            # Visual bar for score
                            bar_len = int(score * 10)
                            bar = "█" * bar_len + "░" * (10 - bar_len)
                            
                            assoc_data.append({
                                "Disease": a['disease_name'],
                                "Association Score": f"{score:.2f}",
                                "Strength": bar
                            })
                        
                        st.dataframe(
                            pd.DataFrame(assoc_data),
                            column_config={
                                "Association Score": st.column_config.NumberColumn(
                                    "Score (0-1)",
                                    help="Open Targets Association Score",
                                    format="%.2f"
                                ),
                            },
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("No disease associations found in Open Targets.")

    st.markdown("---")
    st.caption("Data Sources: ChEMBL (Targets), Open Targets (Disease Associations), UniProt (Descriptions)")
