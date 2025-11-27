"""
OpenTargets Data Ingestion Script
Validates targets against specific diseases (Depression, Anxiety, ADHD) by fetching association scores.
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

OPENTARGETS_GRAPHQL_URL = "https://api.platform.opentargets.org/api/v4/graphql"

# Disease EFO IDs
DISEASES = {
    'Depression': 'EFO_0000426', # Major Depressive Disorder (more specific) or EFO_0003761 (Depression)
    'Anxiety': 'EFO_0000251',
    'ADHD': 'EFO_0003888'
}

def get_target_disease_association(ensembl_id: str, efo_id: str) -> Optional[float]:
    """
    Get association score between a target (Ensembl ID) and a disease (EFO ID).
    Note: OpenTargets uses Ensembl IDs, not UniProt. We might need to map.
    For this MVP, we'll try to use the target symbol to find the Ensembl ID first.
    """
    
    # 1. Get Ensembl ID from Symbol if we don't have it
    # This is a simplified approach. Ideally we'd store Ensembl IDs.
    pass

def get_ensembl_id(symbol: str) -> Optional[str]:
    """
    Get Ensembl ID for a gene symbol using OpenTargets API.
    """
    query = """
    query Search($queryString: String!) {
      search(queryString: $queryString, entityNames: ["target"], page: {index: 0, size: 1}) {
        hits {
          id
          name
        }
      }
    }
    """
    variables = {"queryString": symbol}
    try:
        response = requests.post(OPENTARGETS_GRAPHQL_URL, json={"query": query, "variables": variables})
        response.raise_for_status()
        data = response.json()
        hits = data.get('data', {}).get('search', {}).get('hits', [])
        if hits:
            return hits[0]['id']
        return None
    except Exception as e:
        logger.error("Error searching OpenTargets", symbol=symbol, error=str(e), response=response.text if 'response' in locals() else 'No response')
        return None

def get_association_score(ensembl_id: str, efo_id: str) -> float:
    """
    Get overall association score.
    """
    query = """
    query Association($targetId: String!) {
      target(ensemblId: $targetId) {
        associatedDiseases {
          rows {
            disease {
              id
            }
            score
          }
        }
      }
    }
    """
    variables = {"targetId": ensembl_id}
    try:
        response = requests.post(OPENTARGETS_GRAPHQL_URL, json={"query": query, "variables": variables})
        response.raise_for_status()
        data = response.json()
        rows = data.get('data', {}).get('target', {}).get('associatedDiseases', {}).get('rows', [])
        
        for row in rows:
            if row.get('disease', {}).get('id') == efo_id:
                return row.get('score', 0.0)
        return 0.0
    except Exception as e:
        logger.error("Error fetching association", target=ensembl_id, disease=efo_id, error=str(e), response=response.text if 'response' in locals() else 'No response')
        return 0.0

def ingest_opentargets():
    """
    Iterate over targets, find their Ensembl IDs, and get scores for our diseases.
    """
    client = get_client()
    
    targets = client.client.table('targets').select('id, symbol').execute()
    
    if not targets.data:
        logger.info("No targets found.")
        return

    logger.info(f"Found {len(targets.data)} targets to validate.")

    for target in targets.data:
        symbol = target['symbol']
        target_id = target['id']
        
        # 1. Get Ensembl ID
        ensembl_id = get_ensembl_id(symbol)
        if not ensembl_id:
            logger.warning("Could not find Ensembl ID", symbol=symbol)
            continue
            
        logger.info("Found Ensembl ID", symbol=symbol, ensembl_id=ensembl_id)
        
        # 2. Get scores for each disease
        max_score = 0.0
        for disease_name, efo_id in DISEASES.items():
            score = get_association_score(ensembl_id, efo_id)
            if score > max_score:
                max_score = score
            
            if score > 0:
                logger.info("Found association", symbol=symbol, disease=disease_name, score=score)
        
        # 3. Update target with max evidence score
        # In a real app, we'd store the per-disease score in a junction table
        # For now, we just want to know if it's "validated" for ANY of our indications
        client.client.table('targets').update({'evidence_score': max_score}).eq('id', target_id).execute()

if __name__ == "__main__":
    ingest_opentargets()
