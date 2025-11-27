"""
ClinicalTrials.gov Ingestion Script
Fetches recruiting studies for target indications and ingests the associated drugs.
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

CT_BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

INDICATIONS = ["Depression", "Anxiety", "ADHD"]

def get_recruiting_drugs(indication: str) -> Set[str]:
    """
    Get drugs from recruiting studies for an indication.
    """
    drugs = set()
    next_page_token = None
    
    params = {
        "query.cond": indication,
        "filter.overallStatus": "RECRUITING",
        "pageSize": 50, # Max page size
        "fields": "protocolSection.armsInterventionsModule"
    }
    
    try:
        # Fetch first page
        response = requests.get(CT_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        studies = data.get('studies', [])
        for study in studies:
            interventions = study.get('protocolSection', {}).get('armsInterventionsModule', {}).get('interventions', [])
            for intervention in interventions:
                if intervention.get('type') == 'DRUG':
                    name = intervention.get('name')
                    if name:
                        drugs.add(name)
                        
        logger.info(f"Found {len(drugs)} unique drugs for {indication} (Page 1)")
        
        # We could paginate, but for MVP/Expansion, first 50 studies is a good start
        return drugs
        
    except Exception as e:
        logger.error("Error fetching clinical trials", indication=indication, error=str(e))
        return set()

def ingest_clinical_trials_drugs():
    """
    Main function to ingest drugs from ClinicalTrials.gov.
    """
    all_drugs = set()
    
    for indication in INDICATIONS:
        logger.info(f"Fetching recruiting drugs for {indication}...")
        drugs = get_recruiting_drugs(indication)
        all_drugs.update(drugs)
        
    logger.info(f"Total unique recruiting drugs to ingest: {len(all_drugs)}")
    
    count = 0
    for drug_name in all_drugs:
        try:
            # Clean up name (remove dosage, etc. if possible, but ChEMBL search handles some fuzzy matching)
            # Simple heuristic: take first 3 words if long? No, let's try exact first.
            
            logger.info(f"Ingesting {drug_name}...")
            ingest_drug(drug_name, tier='Silver')
            count += 1
            if count >= 30: # Limit for now
                logger.info("Reached limit of 30 drugs. Stopping.")
                break
        except Exception as e:
            logger.error("Failed to ingest drug", name=drug_name, error=str(e))

if __name__ == "__main__":
    ingest_clinical_trials_drugs()
