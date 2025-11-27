"""
Neuropsych OpenFDA Safety Ingestion

Fetches adverse event data from OpenFDA Drug Adverse Event API for neuropsych drugs.
Writes to the `adverse_events` table linked to `drugs`.

Uses IngestionBase for checkpointing, rate limiting, and validation.

Usage:
    python ingestion/neuropsych_openfda.py
    python ingestion/neuropsych_openfda.py --test  # Process only 5 drugs
    python ingestion/neuropsych_openfda.py --resume  # Resume from checkpoint
    python ingestion/neuropsych_openfda.py --drug "fluoxetine"  # Single drug
"""

import os
import sys
import requests
import time
import argparse
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import structlog
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.ingestion_base import IngestionBase
from core.supabase_client import get_client

load_dotenv()
logger = structlog.get_logger()


class OpenFDAClient:
    """Client for OpenFDA Drug Adverse Event API"""

    BASE_URL = "https://api.fda.gov/drug/event.json"

    def __init__(self, rate_limiter):
        """
        Initialize API client.

        Args:
            rate_limiter: Shared rate limiter
        """
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "pilldreams/1.0 (neuropsych drug intelligence)"
        })
        self.rate_limiter = rate_limiter

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
        self.rate_limiter.wait()

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

    def get_top_adverse_events(
        self,
        drug_name: str,
        top_n: int = 100
    ) -> List[Dict]:
        """
        Get top adverse events by count for a drug using aggregation API.

        Args:
            drug_name: Drug name to search
            top_n: Number of top events to return

        Returns:
            List of {term, count}
        """
        self.rate_limiter.wait()

        # Build query
        query = f'patient.drug.medicinalproduct:"{drug_name}"'

        params = {
            "search": query,
            "count": "patient.reaction.reactionmeddrapt.exact",
            "limit": top_n
        }

        try:
            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                return [
                    {"term": r.get("term", ""), "count": r.get("count", 0)}
                    for r in results
                ]
            elif response.status_code == 404:
                return []
            else:
                logger.error("API error getting top events", drug=drug_name, status=response.status_code)
                return []

        except Exception as e:
            logger.error("Failed to get top events", drug=drug_name, error=str(e))
            return []

    def aggregate_adverse_events(self, reports: List[Dict]) -> Dict[str, Dict]:
        """
        Aggregate adverse events by MedDRA term from raw reports.

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

    def get_serious_event_count(
        self,
        drug_name: str,
        meddra_term: str
    ) -> int:
        """
        Get count of serious events for a specific drug + event combination.

        Args:
            drug_name: Drug name
            meddra_term: Adverse event term

        Returns:
            Count of serious reports
        """
        self.rate_limiter.wait()

        # Build query for serious cases with this drug and event
        query = f'patient.drug.medicinalproduct:"{drug_name}" AND patient.reaction.reactionmeddrapt.exact:"{meddra_term}" AND serious:1'

        params = {
            "search": query,
            "limit": 1
        }

        try:
            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("meta", {}).get("results", {}).get("total", 0)
            return 0

        except Exception as e:
            logger.error("Failed to get serious count", drug=drug_name, term=meddra_term, error=str(e))
            return 0

    def calculate_prr(
        self,
        drug_event_count: int,
        drug_total_reports: int,
        background_event_count: int,
        background_total_reports: int
    ) -> float:
        """
        Calculate Proportional Reporting Ratio (PRR) for disproportionality analysis.

        PRR > 2 with Chi-square > 4 and N >= 3 suggests potential signal.

        Args:
            drug_event_count: Count of reports with this drug + event
            drug_total_reports: Total reports for this drug
            background_event_count: Total reports with this event across all drugs
            background_total_reports: Total reports in database

        Returns:
            PRR value (0 if insufficient data)
        """
        # Avoid division by zero and insufficient data
        if drug_total_reports == 0 or background_total_reports == 0:
            return 0.0

        if drug_event_count < 3:  # Minimum threshold
            return 0.0

        # Calculate background rate (excluding this drug's reports)
        other_event_count = max(0, background_event_count - drug_event_count)
        other_total = max(0, background_total_reports - drug_total_reports)

        if other_total == 0:
            return 0.0

        # PRR calculation
        drug_rate = drug_event_count / drug_total_reports
        background_rate = other_event_count / other_total if other_total > 0 else 0

        if background_rate == 0:
            return 0.0

        prr = drug_rate / background_rate
        return round(prr, 2)


class NeuropsychOpenFDAIngestion(IngestionBase):
    """
    OpenFDA safety data ingestion for neuropsych drugs.

    Reads from `drugs` table, writes to `adverse_events`.
    """

    def __init__(self):
        super().__init__(
            source_name='neuropsych_openfda',
            rate_limit=4.0  # 4 requests/second (240/minute)
        )
        self.api = OpenFDAClient(self.rate_limiter)

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
        Fetch OpenFDA safety data for a drug.

        Args:
            item: Drug record with name

        Returns:
            Dict with top adverse events and total report count
        """
        drug_name = item['name']

        # Normalize drug name for API query
        normalized_name = self.normalize_drug_name(drug_name)

        # Get top adverse events using aggregation API (more efficient)
        top_events = self.api.get_top_adverse_events(normalized_name, top_n=50)

        if not top_events:
            return None

        # Get total report count
        response = self.api.search_adverse_events(normalized_name, limit=1)
        total_reports = response.get("meta", {}).get("results", {}).get("total", 0)

        return {
            'top_events': top_events,
            'total_reports': total_reports
        }

    def process_item(self, item: Dict[str, Any]) -> Tuple[bool, int, int]:
        """
        Process a single drug - fetch OpenFDA data and store adverse events.

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
            # Fetch OpenFDA data
            data = self.fetch_data(item)

            if not data or not data.get('top_events'):
                return (True, 0, 0)  # No data is not a failure

            top_events = data['top_events']
            total_reports = data['total_reports']

            now = datetime.now().isoformat()

            # Process each adverse event
            for event in top_events:
                meddra_term = event['term']
                case_count = event['count']

                if not meddra_term or case_count == 0:
                    continue

                try:
                    # Check if adverse event record exists (schema uses event_name not meddra_term)
                    existing = self.db.client.table('adverse_events').select('id').eq(
                        'drug_id', drug_id
                    ).eq('event_name', meddra_term).execute()

                    # Calculate frequency (approximate - percentage of reports mentioning this event)
                    frequency = (case_count / total_reports * 100) if total_reports > 0 else 0

                    # Calculate seriousness score (0-100)
                    # Based on frequency and common serious events
                    serious_events = [
                        'DEATH', 'SUICIDE', 'COMPLETED SUICIDE', 'SUICIDE ATTEMPT',
                        'SUICIDAL IDEATION', 'CARDIAC ARREST', 'MYOCARDIAL INFARCTION',
                        'STROKE', 'SEIZURE', 'ANAPHYLACTIC', 'SEROTONIN SYNDROME'
                    ]

                    is_serious = any(term.upper() in meddra_term.upper() for term in serious_events)

                    if is_serious:
                        seriousness_score = min(100, 50 + frequency * 5)  # 50-100 range for serious
                    else:
                        seriousness_score = min(50, frequency * 2)  # 0-50 range for non-serious

                    adverse_event_data = {
                        'drug_id': drug_id,
                        'event_name': meddra_term,
                        'frequency': round(frequency, 2),
                        'seriousness_score': round(seriousness_score, 2),
                        'source': 'openfda'
                    }

                    if existing.data:
                        # Update existing
                        self.db.client.table('adverse_events').update(
                            adverse_event_data
                        ).eq('id', existing.data[0]['id']).execute()
                        records_updated += 1
                    else:
                        # Insert new
                        adverse_event_data['created_at'] = now
                        self.db.client.table('adverse_events').insert(adverse_event_data).execute()
                        records_created += 1

                except Exception as e:
                    logger.error(
                        "Failed to insert adverse event",
                        drug=drug_name,
                        term=meddra_term,
                        error=str(e)
                    )

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
        Run the OpenFDA safety data ingestion.

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
        description="Ingest OpenFDA safety data for neuropsych drugs"
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

    pipeline = NeuropsychOpenFDAIngestion()
    result = pipeline.run_ingestion(
        max_drugs=max_drugs,
        single_drug=args.drug,
        resume=resume
    )

    print("\n=== Ingestion Complete ===")
    print(f"Source: {result.get('source', 'neuropsych_openfda')}")
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
