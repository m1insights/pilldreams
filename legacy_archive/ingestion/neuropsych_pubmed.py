"""
Neuropsych PubMed Evidence Ingestion

Fetches evidence classification data from PubMed E-utilities API for neuropsych drugs.
Writes to the `publications` table linked to `drugs`.

Uses IngestionBase for checkpointing, rate limiting, and validation.

Usage:
    python ingestion/neuropsych_pubmed.py
    python ingestion/neuropsych_pubmed.py --test  # Process only 5 drugs
    python ingestion/neuropsych_pubmed.py --resume  # Resume from checkpoint
    python ingestion/neuropsych_pubmed.py --drug "fluoxetine"  # Single drug
"""

import os
import sys
import requests
import time
import argparse
import statistics
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
import structlog
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.ingestion_base import IngestionBase
from core.supabase_client import get_client

load_dotenv()
logger = structlog.get_logger()


class PubMedClient:
    """Client for PubMed E-utilities API"""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, rate_limiter, email: str = "pilldreams@example.com", tool: str = "pilldreams"):
        """
        Initialize API client.

        Args:
            rate_limiter: Shared rate limiter
            email: Valid email address (required by NCBI)
            tool: Application name (required by NCBI)
        """
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"{tool}/1.0"
        })
        self.email = email
        self.tool = tool
        self.rate_limiter = rate_limiter

    def search_articles(
        self,
        drug_name: str,
        publication_type: Optional[str] = None,
        max_results: int = 1000
    ) -> List[str]:
        """
        Search for articles by drug name.

        Args:
            drug_name: Drug name to search
            publication_type: Filter by publication type (e.g., "Randomized Controlled Trial", "Meta-Analysis")
            max_results: Maximum number of results to return

        Returns:
            List of PubMed IDs (PMIDs)
        """
        self.rate_limiter.wait()

        url = f"{self.BASE_URL}/esearch.fcgi"

        # Build query
        query = f'"{drug_name}"[Title/Abstract]'
        if publication_type:
            query += f' AND "{publication_type}"[Publication Type]'

        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "xml",
            "email": self.email,
            "tool": self.tool
        }

        try:
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code != 200:
                logger.error(
                    "PubMed search failed",
                    drug=drug_name,
                    status_code=response.status_code,
                    response=response.text[:500]
                )
                return []

            # Parse XML response
            root = ET.fromstring(response.content)
            id_list = root.find("IdList")

            if id_list is None:
                return []

            pmids = [id_elem.text for id_elem in id_list.findall("Id")]
            logger.debug(
                "Found articles",
                drug=drug_name,
                pub_type=publication_type or "all",
                count=len(pmids)
            )
            return pmids

        except Exception as e:
            logger.error("Failed to search PubMed", drug=drug_name, error=str(e))
            return []

    def get_total_count(self, drug_name: str) -> int:
        """
        Get total article count for a drug (not just RCTs/meta-analyses).

        Args:
            drug_name: Drug name to search

        Returns:
            Total number of articles
        """
        self.rate_limiter.wait()

        url = f"{self.BASE_URL}/esearch.fcgi"

        # Build query - just the drug name in title/abstract
        query = f'"{drug_name}"[Title/Abstract]'

        params = {
            "db": "pubmed",
            "term": query,
            "rettype": "count",
            "retmode": "xml",
            "email": self.email,
            "tool": self.tool
        }

        try:
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code != 200:
                return 0

            # Parse XML response
            root = ET.fromstring(response.content)
            count_elem = root.find("Count")

            if count_elem is not None and count_elem.text:
                return int(count_elem.text)

            return 0

        except Exception as e:
            logger.error("Failed to get total count", drug=drug_name, error=str(e))
            return 0

    def fetch_publication_years(self, pmids: List[str]) -> List[int]:
        """
        Fetch publication years for a list of PMIDs.

        Args:
            pmids: List of PubMed IDs

        Returns:
            List of publication years
        """
        if not pmids:
            return []

        # Split into batches of 100 (API limit)
        batch_size = 100
        all_years = []

        for i in range(0, len(pmids), batch_size):
            self.rate_limiter.wait()

            batch_pmids = pmids[i:i + batch_size]
            pmid_str = ",".join(batch_pmids)

            url = f"{self.BASE_URL}/efetch.fcgi"
            params = {
                "db": "pubmed",
                "id": pmid_str,
                "retmode": "xml",
                "rettype": "medline",
                "email": self.email,
                "tool": self.tool
            }

            try:
                response = self.session.get(url, params=params, timeout=60)

                if response.status_code != 200:
                    logger.error("Failed to fetch article details", status_code=response.status_code)
                    continue

                # Parse XML and extract publication years
                root = ET.fromstring(response.content)
                articles = root.findall(".//PubmedArticle")

                for article in articles:
                    # Try different year paths (PubMed XML can vary)
                    year_elem = article.find(".//PubDate/Year")
                    if year_elem is None:
                        year_elem = article.find(".//PubDate/MedlineDate")

                    if year_elem is not None and year_elem.text:
                        try:
                            # Extract first 4 digits (handles "2020", "2020 Jan", etc.)
                            year_text = year_elem.text.strip()
                            year = int(year_text[:4])
                            if 1900 <= year <= 2100:  # Sanity check
                                all_years.append(year)
                        except (ValueError, TypeError):
                            continue

            except Exception as e:
                logger.error("Failed to fetch batch", error=str(e))
                continue

        return all_years

    def classify_evidence(self, drug_name: str) -> Dict:
        """
        Classify evidence strength for a drug.

        Args:
            drug_name: Drug name to analyze

        Returns:
            Dict with evidence metrics
        """
        logger.debug("Classifying evidence", drug=drug_name)

        # Get total article count
        total_count = self.get_total_count(drug_name)

        # Search for RCTs
        rct_pmids = self.search_articles(
            drug_name,
            publication_type="Randomized Controlled Trial"
        )

        # Search for meta-analyses
        meta_pmids = self.search_articles(
            drug_name,
            publication_type="Meta-Analysis"
        )

        # Combine all PMIDs for publication year analysis
        all_pmids = list(set(rct_pmids + meta_pmids))

        # Fetch publication years (sample if too many)
        sample_pmids = all_pmids[:200]  # Sample for year calculation
        pub_years = self.fetch_publication_years(sample_pmids)

        # Calculate median publication year
        median_year = None
        if pub_years:
            median_year = int(statistics.median(pub_years))

        return {
            "pubmed_count": total_count,
            "n_rcts": len(rct_pmids),
            "n_meta_analyses": len(meta_pmids),
            "median_pub_year": median_year,
            "all_pmids": all_pmids
        }


class NeuropsychPubMedIngestion(IngestionBase):
    """
    PubMed evidence ingestion for neuropsych drugs.

    Reads from `drugs` table, writes to `publications`.
    """

    def __init__(self):
        super().__init__(
            source_name='neuropsych_pubmed',
            rate_limit=3.0  # 3 requests/second (conservative without API key)
        )
        self.api = PubMedClient(self.rate_limiter)

    def get_neuropsych_drugs(self) -> List[Dict[str, Any]]:
        """
        Fetch all drugs from the neuropsych-focused `drugs` table.

        Returns:
            List of drug records with id, name
        """
        drugs = []
        page_size = 1000
        offset = 0

        while True:
            response = self.db.client.table('drugs').select(
                'id, name, tier'
            ).range(offset, offset + page_size - 1).execute()

            if not response.data:
                break

            drugs.extend(response.data)

            if len(response.data) < page_size:
                break

            offset += page_size

        logger.info("Fetched neuropsych drugs", count=len(drugs))
        return drugs

    def fetch_data(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fetch PubMed evidence data for a drug.

        Args:
            item: Drug record with name

        Returns:
            Dict with evidence metrics
        """
        drug_name = item['name']

        # Normalize drug name for API query
        normalized_name = self.normalize_drug_name(drug_name)

        # Classify evidence
        evidence = self.api.classify_evidence(normalized_name)

        return evidence

    def process_item(self, item: Dict[str, Any]) -> Tuple[bool, int, int]:
        """
        Process a single drug - fetch PubMed data and store evidence.

        Args:
            item: Drug record from `drugs` table

        Returns:
            (success, records_created, records_updated)
        """
        drug_id = item['id']
        drug_name = item['name']
        records_created = 0
        records_updated = 0

        try:
            # Fetch PubMed data
            evidence = self.fetch_data(item)

            if not evidence:
                return (True, 0, 0)

            now = datetime.now().isoformat()

            # Check if publication record exists
            existing = self.db.client.table('publications').select('id').eq(
                'drug_id', drug_id
            ).execute()

            # Convert median year to date format if available
            latest_pub_date = None
            if evidence['median_pub_year']:
                latest_pub_date = f"{evidence['median_pub_year']}-01-01"

            publication_data = {
                'drug_id': drug_id,
                'pubmed_count': evidence['pubmed_count'],
                'rct_count': evidence['n_rcts'],
                'meta_analysis_count': evidence['n_meta_analyses'],
                'latest_publication_date': latest_pub_date,
                'updated_at': now
            }

            if existing.data:
                # Update existing
                self.db.client.table('publications').update(
                    publication_data
                ).eq('id', existing.data[0]['id']).execute()
                records_updated = 1
            else:
                # Insert new
                publication_data['created_at'] = now
                self.db.client.table('publications').insert(publication_data).execute()
                records_created = 1

            return (True, records_created, records_updated)

        except Exception as e:
            logger.error("Failed to process drug", drug=drug_name, error=str(e))
            return (False, 0, 0)

    def run_ingestion(
        self,
        max_drugs: Optional[int] = None,
        single_drug: Optional[str] = None,
        resume: bool = True
    ) -> Dict[str, Any]:
        """
        Run the PubMed evidence ingestion.

        Args:
            max_drugs: Maximum number of drugs to process
            single_drug: Process only this specific drug
            resume: Resume from checkpoint

        Returns:
            Summary dict with counts
        """
        # Get drugs to process
        if single_drug:
            drugs = self.db.client.table('drugs').select(
                'id, name, tier'
            ).ilike('name', f'%{single_drug}%').execute().data

            if not drugs:
                logger.error("Drug not found", drug=single_drug)
                return {'error': f'Drug not found: {single_drug}'}

            logger.info(f"Processing single drug: {drugs[0]['name']}")
        else:
            drugs = self.get_neuropsych_drugs()

            if max_drugs:
                drugs = drugs[:max_drugs]

        if not drugs:
            logger.warning("No drugs found to process")
            return {'error': 'No drugs found'}

        # Run ingestion
        return self.run(drugs, resume=resume)


def main():
    parser = argparse.ArgumentParser(
        description="Ingest PubMed evidence data for neuropsych drugs"
    )
    parser.add_argument(
        '--max-drugs',
        type=int,
        default=None,
        help="Maximum number of drugs to process (default: all)"
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help="Test mode: process only 5 drugs"
    )
    parser.add_argument(
        '--drug',
        type=str,
        default=None,
        help="Process a single specific drug by name"
    )
    parser.add_argument(
        '--no-resume',
        action='store_true',
        help="Don't resume from checkpoint, start fresh"
    )

    args = parser.parse_args()

    max_drugs = 5 if args.test else args.max_drugs
    resume = not args.no_resume

    pipeline = NeuropsychPubMedIngestion()
    result = pipeline.run_ingestion(
        max_drugs=max_drugs,
        single_drug=args.drug,
        resume=resume
    )

    print("\n=== Ingestion Complete ===")
    print(f"Source: {result.get('source', 'neuropsych_pubmed')}")
    print(f"Total drugs: {result.get('total', 0)}")
    print(f"Successful: {result.get('successful', 0)}")
    print(f"Failed: {result.get('failed', 0)}")
    print(f"Duration: {result.get('duration_seconds', 0):.1f}s")

    if result.get('errors'):
        print("\nErrors:")
        for err in result['errors'][:5]:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
