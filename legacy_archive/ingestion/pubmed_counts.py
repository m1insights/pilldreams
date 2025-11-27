"""
PubMed Ingestion Script
Fetches publication counts (Total, RCT, Meta-Analysis) for drugs using NCBI E-utilities.
"""

import os
import sys
import requests
import time
import structlog
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.supabase_client import get_client

logger = structlog.get_logger()

EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

def get_pubmed_counts(term: str) -> Dict[str, int]:
    """
    Get publication counts for a term.
    """
    counts = {
        'total': 0,
        'rct': 0,
        'meta_analysis': 0
    }
    
    # 1. Total Count
    try:
        params = {
            'db': 'pubmed',
            'term': f"{term}",
            'retmode': 'json',
            'rettype': 'count'
        }
        response = requests.get(EUTILS_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        counts['total'] = int(data.get('esearchresult', {}).get('count', 0))
        time.sleep(0.34) # Rate limit (3 req/s)
    except Exception as e:
        logger.error("Error fetching total count", term=term, error=str(e))

    # 2. RCT Count
    try:
        params = {
            'db': 'pubmed',
            'term': f"{term} AND (Randomized Controlled Trial[ptyp])",
            'retmode': 'json',
            'rettype': 'count'
        }
        response = requests.get(EUTILS_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        counts['rct'] = int(data.get('esearchresult', {}).get('count', 0))
        time.sleep(0.34)
    except Exception as e:
        logger.error("Error fetching RCT count", term=term, error=str(e))

    # 3. Meta-Analysis Count
    try:
        params = {
            'db': 'pubmed',
            'term': f"{term} AND (Meta-Analysis[ptyp])",
            'retmode': 'json',
            'rettype': 'count'
        }
        response = requests.get(EUTILS_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        counts['meta_analysis'] = int(data.get('esearchresult', {}).get('count', 0))
        time.sleep(0.34)
    except Exception as e:
        logger.error("Error fetching Meta-Analysis count", term=term, error=str(e))
        
    return counts

def ingest_pubmed_counts():
    """
    Main function to ingest PubMed counts for all drugs.
    """
    client = get_client()
    
    # Fetch all drugs
    drugs = client.client.table('drugs').select('id, name').execute().data
    logger.info(f"Found {len(drugs)} drugs to process.")
    
    for drug in drugs:
        drug_id = drug['id']
        drug_name = drug['name']
        
        logger.info(f"Processing {drug_name}...")
        
        counts = get_pubmed_counts(drug_name)
        logger.info("Fetched counts", drug=drug_name, counts=counts)
        
        # Upsert into publications table
        # Check if record exists
        existing = client.client.table('publications').select('id').eq('drug_id', drug_id).execute().data
        
        record = {
            'drug_id': drug_id,
            'pubmed_count': counts['total'],
            'rct_count': counts['rct'],
            'meta_analysis_count': counts['meta_analysis'],
            'updated_at': datetime.now().isoformat()
        }
        
        if existing:
            client.client.table('publications').update(record).eq('id', existing[0]['id']).execute()
        else:
            client.client.table('publications').insert(record).execute()
            
if __name__ == "__main__":
    ingest_pubmed_counts()
