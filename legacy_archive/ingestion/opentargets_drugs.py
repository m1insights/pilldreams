"""
OpenTargets Drug Ingestion Script
Fetches known drugs for target indications and ingests them into the database.
"""

import os
import sys
import requests
import structlog
from typing import Dict, Any, List, Set

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.chembl import ingest_drug

logger = structlog.get_logger()

OPENTARGETS_GRAPHQL_URL = "https://api.platform.opentargets.org/api/v4/graphql"

# Disease IDs
DISEASES = {
    'Depression': 'MONDO_0002009', # Major Depressive Disorder
    'Anxiety': 'EFO_0006788',      # Anxiety Disorder
    'ADHD': 'EFO_0003888'          # ADHD
}

def get_known_drugs(disease_id: str) -> List[Dict[str, str]]:
    """
    Get known drugs for a disease from OpenTargets.
    """
    query = """
    query DiseaseDrugs($diseaseId: String!) {
      disease(efoId: $diseaseId) {
        knownDrugs {
          rows {
            drug {
              id
              name
            }
            phase
            status
          }
        }
      }
    }
    """
    variables = {"diseaseId": disease_id}
    try:
        response = requests.post(OPENTARGETS_GRAPHQL_URL, json={"query": query, "variables": variables})
        response.raise_for_status()
        data = response.json()
        rows = data.get('data', {}).get('disease', {}).get('knownDrugs', {}).get('rows', [])
        
        drugs = []
        seen_ids = set()
        
        for row in rows:
            drug = row.get('drug', {})
            chembl_id = drug.get('id')
            name = drug.get('name')
            phase = row.get('phase')
            
            # Filter: Only Phase 2+ (Reliability Tier: Silver)
            if phase and phase < 2:
                continue
                
            if chembl_id and chembl_id not in seen_ids:
                drugs.append({'id': chembl_id, 'name': name})
                seen_ids.add(chembl_id)
                
        return drugs
    except Exception as e:
        logger.error("Error fetching known drugs", disease_id=disease_id, error=str(e))
        return []

def ingest_opentargets_drugs():
    """
    Main function to ingest drugs from OpenTargets.
    """
    all_drugs = {} # Map ID -> Name
    
    for disease, efo_id in DISEASES.items():
        logger.info(f"Fetching drugs for {disease} ({efo_id})...")
        drugs = get_known_drugs(efo_id)
        logger.info(f"Found {len(drugs)} drugs for {disease}")
        
        for d in drugs:
            all_drugs[d['id']] = d['name']
            
    logger.info(f"Total unique drugs to ingest: {len(all_drugs)}")
    
    count = 0
    for chembl_id, name in all_drugs.items():
        try:
            logger.info(f"Ingesting {name} ({chembl_id})...")
            ingest_drug(name, chembl_id=chembl_id, tier='Silver')
            count += 1
            if count >= 50: # Limit for now to avoid rate limits/long run
                logger.info("Reached limit of 50 drugs. Stopping.")
                break
        except Exception as e:
            logger.error("Failed to ingest drug", name=name, error=str(e))

if __name__ == "__main__":
    ingest_opentargets_drugs()
