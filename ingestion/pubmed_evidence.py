"""
PubMed Evidence Strength Ingestion Script

Fetches evidence classification data from PubMed E-utilities API for evidence maturity scoring.

API Documentation: https://www.ncbi.nlm.nih.gov/books/NBK25499/
"""

import os
import sys
import requests
import time
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import structlog
from dotenv import load_dotenv
import statistics

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.supabase_client import get_client
from core.drug_name_utils import normalize_drug_name

load_dotenv()
logger = structlog.get_logger()


class PubMedClient:
    """Client for PubMed E-utilities API"""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    # Rate limits: 3 requests/second without API key, 10/second with key
    REQUESTS_PER_SECOND = 3  # Conservative (no API key)
    RATE_LIMIT_DELAY = 1.0 / REQUESTS_PER_SECOND  # ~0.33 seconds

    def __init__(self, email: str = "pilldreams@example.com", tool: str = "pilldreams"):
        """
        Initialize API client.

        Args:
            email: Valid email address (required by NCBI)
            tool: Application name (required by NCBI)
        """
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"{tool}/1.0"
        })
        self.email = email
        self.tool = tool
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()

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
        self._rate_limit()

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

        self._rate_limit()

        url = f"{self.BASE_URL}/efetch.fcgi"

        # Split into batches of 100 (API limit)
        batch_size = 100
        all_years = []

        for i in range(0, len(pmids), batch_size):
            batch_pmids = pmids[i:i + batch_size]
            pmid_str = ",".join(batch_pmids)

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

                self._rate_limit()  # Rate limit between batches

            except Exception as e:
                logger.error("Failed to fetch batch", error=str(e))
                continue

        return all_years


class EvidenceIngestionPipeline:
    """Pipeline for ingesting PubMed evidence data into Supabase"""

    def __init__(self):
        """Initialize pipeline"""
        self.api = PubMedClient()
        self.db = get_client()

    def classify_evidence(self, drug_name: str) -> Dict:
        """
        Classify evidence strength for a drug.

        Args:
            drug_name: Drug name to analyze

        Returns:
            Dict with evidence metrics:
            {
                "n_rcts": int,
                "n_meta_analyses": int,
                "median_pub_year": int or None,
                "all_pmids": List[str]
            }
        """
        logger.debug("Classifying evidence", drug=drug_name)

        # Search for RCTs
        rct_pmids = self.api.search_articles(
            drug_name,
            publication_type="Randomized Controlled Trial"
        )

        # Search for meta-analyses
        meta_pmids = self.api.search_articles(
            drug_name,
            publication_type="Meta-Analysis"
        )

        # Combine all PMIDs for publication year analysis
        all_pmids = list(set(rct_pmids + meta_pmids))

        # Fetch publication years
        pub_years = self.api.fetch_publication_years(all_pmids)

        # Calculate median publication year
        median_year = None
        if pub_years:
            median_year = int(statistics.median(pub_years))

        return {
            "n_rcts": len(rct_pmids),
            "n_meta_analyses": len(meta_pmids),
            "median_pub_year": median_year,
            "all_pmids": all_pmids
        }

    def ingest_evidence_data(self, max_drugs: Optional[int] = None):
        """
        Main ingestion pipeline.

        Args:
            max_drugs: Maximum number of drugs to process (None = all)
        """
        logger.info("Starting PubMed evidence data ingestion", max_drugs=max_drugs or "all")

        # Step 1: Fetch all drugs from database (with pagination)
        # Supabase has 1000 row limit per request
        drugs = []
        page_size = 1000
        offset = 0

        while True:
            drugs_response = self.db.client.table('drug').select('id, name').range(offset, offset + page_size - 1).execute()
            page_data = drugs_response.data

            if not page_data:
                break

            drugs.extend(page_data)
            offset += page_size

            # Break if we got less than page_size (last page)
            if len(page_data) < page_size:
                break

        if not drugs:
            logger.warning("No drugs found in database")
            return

        # Limit if specified
        if max_drugs:
            drugs = drugs[:max_drugs]

        logger.info("Fetched drugs from database", count=len(drugs))

        # Step 2: For each drug, classify evidence
        total_drugs_processed = 0
        total_drugs_with_evidence = 0
        total_rcts = 0
        total_meta_analyses = 0

        for i, drug in enumerate(drugs, 1):
            drug_id = drug["id"]
            drug_name = drug["name"]

            # Normalize drug name for API query (remove dosage info)
            normalized_name = normalize_drug_name(drug_name)

            logger.info(
                "Processing drug",
                index=f"{i}/{len(drugs)}",
                drug=drug_name,
                normalized=normalized_name if normalized_name != drug_name else None
            )

            # Classify evidence using normalized name
            evidence = self.classify_evidence(normalized_name)

            # Step 3: Insert/update EvidenceAggregate
            try:
                # Check if entry exists
                existing = self.db.client.table("evidenceaggregate").select("id").eq(
                    "drug_id", drug_id
                ).execute()

                if existing.data:
                    # Update existing
                    self.db.client.table("evidenceaggregate").update({
                        "n_rcts": evidence["n_rcts"],
                        "n_meta_analyses": evidence["n_meta_analyses"],
                        "median_pub_year": evidence["median_pub_year"]
                    }).eq("id", existing.data[0]["id"]).execute()
                    logger.debug("Updated evidence aggregate", drug=drug_name)
                else:
                    # Insert new
                    self.db.client.table("evidenceaggregate").insert({
                        "drug_id": drug_id,
                        "n_rcts": evidence["n_rcts"],
                        "n_meta_analyses": evidence["n_meta_analyses"],
                        "median_pub_year": evidence["median_pub_year"]
                    }).execute()
                    logger.debug("Inserted evidence aggregate", drug=drug_name)

                total_drugs_processed += 1

                if evidence["n_rcts"] > 0 or evidence["n_meta_analyses"] > 0:
                    total_drugs_with_evidence += 1
                    total_rcts += evidence["n_rcts"]
                    total_meta_analyses += evidence["n_meta_analyses"]

            except Exception as e:
                logger.error(
                    "Failed to insert/update evidence aggregate",
                    drug=drug_name,
                    error=str(e)
                )

        logger.info(
            "PubMed evidence ingestion complete",
            drugs_processed=total_drugs_processed,
            drugs_with_evidence=total_drugs_with_evidence,
            total_rcts=total_rcts,
            total_meta_analyses=total_meta_analyses
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest evidence data from PubMed")
    parser.add_argument(
        "--max-drugs",
        type=int,
        default=None,
        help="Maximum number of drugs to process (default: all)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: process only 5 drugs"
    )

    args = parser.parse_args()

    max_drugs = 5 if args.test else args.max_drugs

    pipeline = EvidenceIngestionPipeline()
    pipeline.ingest_evidence_data(max_drugs=max_drugs)
