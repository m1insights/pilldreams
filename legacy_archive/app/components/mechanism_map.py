import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
from core.supabase_client import get_client

def render_mechanism_map():
    """
    Renders the interactive Mechanism Map.
    """
    client = get_client()
    
    # Fetch Data
    # Limit to top 50 drugs/targets to avoid clutter for MVP
    drugs = client.client.table('drugs').select('id, name, tier').limit(50).execute().data
    targets = client.client.table('targets').select('id, symbol, has_3d_structure').limit(50).execute().data
    drug_targets = client.client.table('drug_targets').select('drug_id, target_id').execute().data
    
    nodes = []
    edges = []
    
    # Helper to track added nodes
    added_node_ids = set()
    
    # Add Targets (Central Nodes)
    for t in targets:
        color = "#FF5722" # Deep Orange
        if t.get('has_3d_structure'):
            color = "#4CAF50" # Green for 3D available
            
        nodes.append(Node(
            id=t['id'], 
            label=t['symbol'], 
            size=25, 
            color=color,
            symbolType="triangle"
        ))
        added_node_ids.add(t['id'])
        
    # Add Drugs (Peripheral Nodes)
    for d in drugs:
        tier = d.get('tier', 'Bronze')
        color = "#607D8B" # Blue Grey
        if tier == 'Gold':
            color = "#FFD700" # Gold
        elif tier == 'Silver':
            color = "#C0C0C0" # Silver
            
        nodes.append(Node(
            id=d['id'], 
            label=d['name'], 
            size=15, 
            color=color,
            symbolType="circle"
        ))
        added_node_ids.add(d['id'])
        
    # Add Edges
    for dt in drug_targets:
        if dt['drug_id'] in added_node_ids and dt['target_id'] in added_node_ids:
            edges.append(Edge(
                source=dt['drug_id'], 
                target=dt['target_id'], 
                color="#999999"
            ))
            
    # Configuration
    config = Config(
        width=800,
        height=600,
        directed=False, 
        physics=True, 
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=False
    )
    
    st.markdown("### 🕸️ Mechanism Map")
    st.markdown("""
    **Legend:**
    - 🟡 **Gold Drug** (Approved)
    - ⚪ **Silver Drug** (Clinical)
    - 🔘 **Bronze Drug** (Emerging)
    - 🔺 **Target** (Green = 3D Structure Available)
    """)
    
    return agraph(nodes=nodes, edges=edges, config=config)
