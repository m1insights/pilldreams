"""
OpenFDA Safety Data Ingestion Script

Fetches adverse event data from OpenFDA Drug Adverse Event API for investor risk analysis.

API Documentation: https://open.fda.gov/apis/drug/event/
"""

import os
import sys
import requests
import time
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import structlog
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.supabase_client import get_client
from core.drug_name_utils import normalize_drug_name

load_dotenv()
logger = structlog.get_logger()


class OpenFDAClient:
    """Client for OpenFDA Drug Adverse Event API"""

    BASE_URL = "https://api.fda.gov/drug/event.json"

    # Rate limits: 240 requests/minute (4 per second)
    REQUESTS_PER_MINUTE = 240
    RATE_LIMIT_DELAY = 60.0 / REQUESTS_PER_MINUTE  # ~0.25 seconds

    def __init__(self):
        """Initialize API client"""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "pilldreams/1.0 (drug intelligence platform)"
        })
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()

    def search_adverse_events(
        self,
        drug_name: str,
        limit: int = 1000
    ) -> Dict:
        """
        Search for adverse events by drug name.

        Args:
            drug_name: Drug name to search
            limit: Maximum number of results (max 1000 per request)

        Returns:
            API response with adverse event data
        """
        self._rate_limit()

        # Build query
        query = f'patient.drug.medicinalproduct:"{drug_name}"'

        params = {
            "search": query,
            "limit": min(limit, 1000)  # API max is 1000
        }

        try:
            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                # No results found - this is normal for many drugs
                logger.debug("No adverse events found", drug=drug_name)
                return {"meta": {"results": {"total": 0}}, "results": []}
            else:
                logger.error(
                    "API error",
                    drug=drug_name,
                    status_code=response.status_code,
                    response=response.text[:500]
                )
                return {"meta": {"results": {"total": 0}}, "results": []}

        except Exception as e:
            logger.error("Failed to fetch adverse events", drug=drug_name, error=str(e))
            return {"meta": {"results": {"total": 0}}, "results": []}

    def aggregate_adverse_events(self, reports: List[Dict]) -> Dict[str, Dict]:
        """
        Aggregate adverse events by MedDRA term.

        Args:
            reports: List of adverse event reports from API

        Returns:
            Dict of {meddra_term: {count, serious_count}}
        """
        aggregated = defaultdict(lambda: {"total": 0, "serious": 0})

        for report in reports:
            # Check if report is serious (serious field == "2" or == "1")
            is_serious = report.get("serious") in ["1", "2"]

            # Extract patient reactions
            patient = report.get("patient", {})
            reactions = patient.get("reaction", [])

            for reaction in reactions:
                # MedDRA term (preferred term)
                meddra_term = reaction.get("reactionmeddrapt", "").strip()

                if meddra_term:
                    aggregated[meddra_term]["total"] += 1
                    if is_serious:
                        aggregated[meddra_term]["serious"] += 1

        return dict(aggregated)

    def calculate_prr(
        self,
        drug_name: str,
        meddra_term: str,
        drug_event_count: int,
        drug_total_reports: int,
        database_event_count: int,
        database_total_reports: int
    ) -> float:
        """
        Calculate Proportional Reporting Ratio (PRR) for disproportionality analysis.

        PRR formula:
        PRR = (a/b) / (c/d)
        where:
        a = # reports with drug and event
        b = # reports with drug
        c = # reports with event (excluding drug)
        d = # total reports (excluding drug)

        PRR > 2 suggests potential signal

        Args:
            drug_name: Drug name
            meddra_term: Adverse event term
            drug_event_count: Count of reports with this drug + event
            drug_total_reports: Total reports for this drug
            database_event_count: Total reports with this event across all drugs
            database_total_reports: Total reports in database

        Returns:
            PRR value (0 if insufficient data)
        """
        # Avoid division by zero
        if drug_total_reports == 0 or database_total_reports == 0:
            return 0.0

        # Calculate background rate (excluding this drug's reports)
        background_event_count = database_event_count - drug_event_count
        background_total = database_total_reports - drug_total_reports

        if background_total == 0 or background_event_count == 0:
            return 0.0

        # PRR calculation
        drug_rate = drug_event_count / drug_total_reports
        background_rate = background_event_count / background_total

        if background_rate == 0:
            return 0.0

        prr = drug_rate / background_rate
        return round(prr, 2)


class SafetyIngestionPipeline:
    """Pipeline for ingesting OpenFDA safety data into Supabase"""

    def __init__(self):
        """Initialize pipeline"""
        self.api = OpenFDAClient()
        self.db = get_client()

    def ingest_safety_data(self, max_drugs: Optional[int] = None):
        """
        Main ingestion pipeline.

        Args:
            max_drugs: Maximum number of drugs to process (None = all)
        """
        logger.info("Starting OpenFDA safety data ingestion", max_drugs=max_drugs or "all")

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

        # Step 2: For each drug, fetch adverse events
        total_drugs_processed = 0
        total_events_inserted = 0
        drugs_with_events = 0

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

            # Fetch adverse events from OpenFDA using normalized name
            response = self.api.search_adverse_events(normalized_name, limit=1000)
            total_reports = response.get("meta", {}).get("results", {}).get("total", 0)
            reports = response.get("results", [])

            if total_reports == 0:
                logger.debug("No adverse events found", drug=drug_name)
                continue

            # Aggregate events by MedDRA term
            aggregated = self.api.aggregate_adverse_events(reports)

            if not aggregated:
                logger.debug("No reactions found in reports", drug=drug_name)
                continue

            drugs_with_events += 1

            # Step 3: Insert into SafetyAggregate table
            for meddra_term, counts in aggregated.items():
                try:
                    # Check if entry exists (table name is lowercase in PostgreSQL)
                    existing = self.db.client.table("safetyaggregate").select("id").eq(
                        "drug_id", drug_id
                    ).eq("meddra_term", meddra_term).execute()

                    if existing.data:
                        # Update existing
                        self.db.client.table("safetyaggregate").update({
                            "case_count": counts["total"],
                            "is_serious": counts["serious"] > 0,
                            "disproportionality_metric": 0.0  # Placeholder for now
                        }).eq("id", existing.data[0]["id"]).execute()
                        logger.debug("Updated safety aggregate", drug=drug_name, term=meddra_term)
                    else:
                        # Insert new
                        self.db.client.table("safetyaggregate").insert({
                            "drug_id": drug_id,
                            "meddra_term": meddra_term,
                            "case_count": counts["total"],
                            "is_serious": counts["serious"] > 0,
                            "disproportionality_metric": 0.0  # Placeholder for now
                        }).execute()
                        total_events_inserted += 1
                        logger.debug("Inserted safety aggregate", drug=drug_name, term=meddra_term)

                except Exception as e:
                    logger.error(
                        "Failed to insert safety aggregate",
                        drug=drug_name,
                        term=meddra_term,
                        error=str(e)
                    )

            total_drugs_processed += 1

        logger.info(
            "Safety data ingestion complete",
            drugs_processed=total_drugs_processed,
            drugs_with_events=drugs_with_events,
            events_inserted=total_events_inserted
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest safety data from OpenFDA")
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

    pipeline = SafetyIngestionPipeline()
    pipeline.ingest_safety_data(max_drugs=max_drugs)
