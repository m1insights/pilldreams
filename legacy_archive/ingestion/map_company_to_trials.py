
import os
import sys
import logging
import time
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.supabase_client import get_client
from ingestion.clinicaltrials import TrialIngestionPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ingestion/sponsor_matching.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def ingest_company_pipelines(limit: int = None):
    """
    Iterates through NBI companies and ingests their clinical trials.
    """
    db = get_client()
    pipeline = TrialIngestionPipeline()
    
    logger.info("Starting NBI company pipeline ingestion...")
    
    # 1. Fetch all NBI companies
    logger.info("Fetching NBI companies...")
    companies_response = db.client.table('company') \
        .select('id, name, ticker') \
        .eq('is_nbi_member', True) \
        .execute()
    
    companies = companies_response.data
    logger.info(f"Found {len(companies)} NBI companies.")
    
    if limit:
        companies = companies[:limit]
        logger.info(f"Limiting to first {limit} companies.")
    
    # 2. Ingest trials for each company
    for i, company in enumerate(companies):
        company_name = company['name']
        company_id = company['id']
        ticker = company['ticker']
        
        logger.info(f"[{i+1}/{len(companies)}] Processing {ticker} - {company_name}...")
        
        try:
            # Clean company name for search (remove Inc, Corp, etc. for better recall?)
            # Actually, CT.gov search is usually better with specific names, but "Moderna, Inc." works.
            # Let's try exact name first.
            
            # Fetch all trials for comprehensive coverage
            pipeline.ingest_trials(max_trials=None, sponsor=company_name, company_id=company_id)
            
            # Sleep to be nice to API
            time.sleep(1.0)
            
        except Exception as e:
            logger.error(f"Error processing {company_name}: {str(e)}")
            
    logger.info("Pipeline ingestion completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest pipelines for NBI companies")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of companies to process")
    args = parser.parse_args()
    
    ingest_company_pipelines(limit=args.limit)
