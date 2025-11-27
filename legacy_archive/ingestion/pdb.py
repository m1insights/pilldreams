"""
PDB Ingestion Script
Checks RCSB PDB for available 3D structures for targets using UniProt IDs.
"""

import os
import sys
import requests
import structlog
from typing import List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.supabase_client import get_client

logger = structlog.get_logger()

RCSB_SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"

def check_pdb_structure(uniprot_id: str) -> bool:
    """
    Check if a UniProt ID has associated PDB structures.
    """
    query = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                "operator": "exact_match",
                "value": uniprot_id
            }
        },
        "return_type": "entry",
        "request_options": {
            "return_all_hits": False,
            "results_verbosity": "compact"
        }
    }
    
    try:
        response = requests.post(RCSB_SEARCH_URL, json=query)
        if response.status_code == 204: # No content = No hits
            return False
        response.raise_for_status()
        data = response.json()
        return data.get('total_count', 0) > 0
    except Exception as e:
        logger.error("Error checking PDB", uniprot_id=uniprot_id, error=str(e))
        return False

def ingest_pdb_data():
    """
    Main function to ingest PDB availability for targets.
    """
    client = get_client()
    
    # Fetch all targets with UniProt IDs
    targets = client.client.table('targets').select('id, symbol, uniprot_id').neq('uniprot_id', None).execute().data
    logger.info(f"Found {len(targets)} targets to process.")
    
    for target in targets:
        target_id = target['id']
        symbol = target['symbol']
        uniprot_id = target['uniprot_id']
        
        logger.info(f"Checking PDB for {symbol} ({uniprot_id})...")
        
        has_structure = check_pdb_structure(uniprot_id)
        
        if has_structure:
            logger.info(f"Found structure for {symbol}")
            client.client.table('targets').update({'has_3d_structure': True}).eq('id', target_id).execute()
        else:
            logger.info(f"No structure for {symbol}")
            
if __name__ == "__main__":
    ingest_pdb_data()
