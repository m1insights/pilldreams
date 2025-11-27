"""
UniProt Data Ingestion Script
Enriches target data with biological function, subcellular location, and GO terms from UniProt.
"""

import os
import sys
import requests
import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.supabase_client import get_client

logger = structlog.get_logger()

UNIPROT_BASE_URL = "https://rest.uniprot.org/uniprotkb"

def get_uniprot_data(uniprot_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed data from UniProt for a given ID.
    """
    url = f"{UNIPROT_BASE_URL}/{uniprot_id}.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("Error fetching UniProt data", uniprot_id=uniprot_id, error=str(e))
        return None

def extract_function(data: Dict[str, Any]) -> str:
    """Extract function description."""
    comments = data.get('comments', [])
    for comment in comments:
        if comment.get('commentType') == 'FUNCTION':
            return comment.get('texts', [{}])[0].get('value', '')
    return ''

def extract_subcellular_location(data: Dict[str, Any]) -> List[str]:
    """Extract subcellular locations."""
    locations = []
    comments = data.get('comments', [])
    for comment in comments:
        if comment.get('commentType') == 'SUBCELLULAR LOCATION':
            for loc in comment.get('subcellularLocations', []):
                val = loc.get('location', {}).get('value')
                if val:
                    locations.append(val)
    return locations

def enrich_targets():
    """
    Iterate over targets in DB and enrich with UniProt data.
    """
    client = get_client()
    
    # Get targets with UniProt IDs
    # Note: In a real scenario, we might need to map ChEMBL IDs to UniProt IDs if missing
    # But our ChEMBL ingestion tries to populate uniprot_id
    targets = client.client.table('targets').select('id, uniprot_id, symbol').not_.is_('uniprot_id', 'null').execute()
    
    if not targets.data:
        logger.info("No targets with UniProt IDs found to enrich.")
        return

    logger.info(f"Found {len(targets.data)} targets to enrich.")

    for target in targets.data:
        uniprot_id = target['uniprot_id']
        target_id = target['id']
        symbol = target['symbol']
        
        logger.info("Enriching target", symbol=symbol, uniprot_id=uniprot_id)
        
        data = get_uniprot_data(uniprot_id)
        if not data:
            continue
            
        function_desc = extract_function(data)
        locations = extract_subcellular_location(data)
        
        # We can store this in the 'description' or a new 'biology' column
        # For now, let's append to description if it's short, or just update description if it's generic
        
        update_data = {
            'description': function_desc[:500] + "..." if len(function_desc) > 500 else function_desc,
            # We could add more fields to the schema for structured data like locations
            # For now, we'll just log it as we don't have a specific column yet
        }
        
        client.client.table('targets').update(update_data).eq('id', target_id).execute()
        logger.info("Updated target", symbol=symbol)

if __name__ == "__main__":
    enrich_targets()
