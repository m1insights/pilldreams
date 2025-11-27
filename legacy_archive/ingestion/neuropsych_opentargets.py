"""
Neuropsych OpenTargets Disease Association Ingestion

Validates targets against neuropsych diseases (Depression, Anxiety, ADHD)
by fetching association scores from OpenTargets Platform API.

Updates targets.evidence_score with the maximum association score across
the three neuropsych indications.

Uses IngestionBase for rate limiting and structured logging.

Usage:
    python ingestion/neuropsych_opentargets.py
    python ingestion/neuropsych_opentargets.py --test  # Process only 5 targets
"""

import os
import sys
import requests
import argparse
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


# OpenTargets disease EFO IDs for neuropsych indications
NEUROPSYCH_DISEASES = {
    'Depression': 'EFO_0003761',  # Depressive disorder
    'Major Depressive Disorder': 'EFO_0000426',  # More specific
    'Anxiety': 'EFO_0000251',  # Anxiety disorder
    'ADHD': 'EFO_0003888',  # Attention deficit hyperactivity disorder
}


class OpenTargetsClient:
    """Client for OpenTargets Platform GraphQL API"""

    GRAPHQL_URL = "https://api.platform.opentargets.org/api/v4/graphql"

    def __init__(self, rate_limiter):
        """
        Initialize API client.

        Args:
            rate_limiter: Shared rate limiter
        """
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "pilldreams/1.0 (neuropsych drug intelligence)",
            "Content-Type": "application/json"
        })
        self.rate_limiter = rate_limiter

    def get_ensembl_id(self, symbol: str) -> Optional[str]:
        """
        Get Ensembl ID for a gene symbol using OpenTargets search.

        Args:
            symbol: Gene symbol (e.g., HTR1A, DRD2)

        Returns:
            Ensembl ID or None
        """
        self.rate_limiter.wait()

        query = """
        query Search($queryString: String!) {
            search(queryString: $queryString, entityNames: ["target"], page: {index: 0, size: 5}) {
                hits {
                    id
                    name
                    entity
                }
            }
        }
        """

        variables = {"queryString": symbol}

        try:
            response = self.session.post(
                self.GRAPHQL_URL,
                json={"query": query, "variables": variables},
                timeout=30
            )

            if response.status_code != 200:
                logger.error(
                    "OpenTargets search failed",
                    symbol=symbol,
                    status_code=response.status_code
                )
                return None

            data = response.json()
            hits = data.get("data", {}).get("search", {}).get("hits", [])

            # Find best match - prefer exact symbol matches
            for hit in hits:
                if hit.get("entity") == "target":
                    hit_name = hit.get("name", "").upper()
                    # Check if symbol is in the name (gene symbols are usually in uppercase)
                    if symbol.upper() in hit_name or hit_name.startswith(symbol.upper()):
                        return hit.get("id")

            # Return first target hit if no exact match
            for hit in hits:
                if hit.get("entity") == "target":
                    return hit.get("id")

            return None

        except Exception as e:
            logger.error("Failed to search OpenTargets", symbol=symbol, error=str(e))
            return None

    def get_disease_associations(
        self,
        ensembl_id: str,
        disease_ids: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Get disease association scores for a target.

        Args:
            ensembl_id: Ensembl gene ID (e.g., ENSG00000157404)
            disease_ids: Optional list of EFO IDs to filter (default: all)

        Returns:
            Dict of {disease_efo_id: association_score}
        """
        self.rate_limiter.wait()

        query = """
        query TargetDiseases($ensemblId: String!) {
            target(ensemblId: $ensemblId) {
                id
                approvedSymbol
                associatedDiseases(page: {index: 0, size: 100}) {
                    count
                    rows {
                        disease {
                            id
                            name
                        }
                        score
                        datatypeScores {
                            id
                            score
                        }
                    }
                }
            }
        }
        """

        variables = {"ensemblId": ensembl_id}

        try:
            response = self.session.post(
                self.GRAPHQL_URL,
                json={"query": query, "variables": variables},
                timeout=60
            )

            if response.status_code != 200:
                logger.error(
                    "OpenTargets query failed",
                    ensembl_id=ensembl_id,
                    status_code=response.status_code
                )
                return {}

            data = response.json()
            target_data = data.get("data", {}).get("target")

            if not target_data:
                return {}

            associations = {}
            rows = target_data.get("associatedDiseases", {}).get("rows", [])

            for row in rows:
                disease = row.get("disease", {})
                disease_id = disease.get("id", "")
                score = row.get("score", 0.0)

                # Filter to specific diseases if requested
                if disease_ids and disease_id not in disease_ids:
                    continue

                associations[disease_id] = score

            return associations

        except Exception as e:
            logger.error(
                "Failed to get disease associations",
                ensembl_id=ensembl_id,
                error=str(e)
            )
            return {}

    def get_neuropsych_score(self, ensembl_id: str) -> Tuple[float, Dict[str, float]]:
        """
        Get neuropsych-specific association scores.

        Args:
            ensembl_id: Ensembl gene ID

        Returns:
            (max_score, {disease_name: score})
        """
        # Get all disease associations
        associations = self.get_disease_associations(ensembl_id)

        if not associations:
            return 0.0, {}

        # Filter to neuropsych diseases
        neuropsych_scores = {}
        efo_to_name = {v: k for k, v in NEUROPSYCH_DISEASES.items()}

        for efo_id, score in associations.items():
            if efo_id in efo_to_name:
                disease_name = efo_to_name[efo_id]
                neuropsych_scores[disease_name] = score

        # Calculate max score
        max_score = max(neuropsych_scores.values()) if neuropsych_scores else 0.0

        return max_score, neuropsych_scores


class NeuropsychOpenTargetsIngestion(IngestionBase):
    """
    OpenTargets disease association ingestion for neuropsych targets.

    Reads from `targets` table, updates evidence_score field.
    """

    def __init__(self):
        super().__init__(
            source_name='neuropsych_opentargets',
            rate_limit=5.0  # 5 requests/second
        )
        self.api = OpenTargetsClient(self.rate_limiter)

    def get_targets_to_validate(self) -> List[Dict[str, Any]]:
        """
        Fetch targets that need OpenTargets validation.

        Returns all targets, prioritizing those without evidence_score.
        """
        targets = []
        page_size = 1000
        offset = 0

        while True:
            response = self.db.client.table('targets').select(
                'id, symbol, uniprot_id, evidence_score'
            ).range(offset, offset + page_size - 1).execute()

            if not response.data:
                break

            targets.extend(response.data)

            if len(response.data) < page_size:
                break

            offset += page_size

        logger.info("Fetched targets for validation", count=len(targets))
        return targets

    def fetch_data(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fetch OpenTargets data for a target.

        Args:
            item: Target record with symbol

        Returns:
            Dict with evidence_score and disease associations
        """
        symbol = item['symbol']

        # Get Ensembl ID
        ensembl_id = self.api.get_ensembl_id(symbol)

        if not ensembl_id:
            logger.debug("No Ensembl ID found", symbol=symbol)
            return None

        # Get neuropsych-specific scores
        max_score, disease_scores = self.api.get_neuropsych_score(ensembl_id)

        return {
            'ensembl_id': ensembl_id,
            'evidence_score': max_score,
            'disease_scores': disease_scores
        }

    def process_item(self, item: Dict[str, Any]) -> Tuple[bool, int, int]:
        """
        Process a single target - fetch OpenTargets data and update.

        Args:
            item: Target record from `targets` table

        Returns:
            (success, records_created, records_updated)
        """
        target_id = item['id']
        symbol = item['symbol']

        try:
            # Fetch OpenTargets data
            data = self.fetch_data(item)

            if not data:
                # No data found - not a failure, just no update
                return (True, 0, 0)

            evidence_score = data.get('evidence_score', 0.0)
            disease_scores = data.get('disease_scores', {})

            # Log disease associations if found
            if disease_scores:
                logger.info(
                    "Found disease associations",
                    symbol=symbol,
                    scores=disease_scores
                )

            # Update evidence_score
            self.db.client.table('targets').update({
                'evidence_score': round(evidence_score, 4)
            }).eq('id', target_id).execute()

            return (True, 0, 1)  # 1 updated

        except Exception as e:
            logger.error("Failed to process target", symbol=symbol, error=str(e))
            return (False, 0, 0)

    def run_ingestion(
        self,
        max_targets: Optional[int] = None,
        resume: bool = True
    ) -> Dict[str, Any]:
        """
        Run the OpenTargets validation.

        Args:
            max_targets: Maximum number of targets to process
            resume: Resume from checkpoint

        Returns:
            Summary dict with counts
        """
        # Get targets to validate
        targets = self.get_targets_to_validate()

        if max_targets:
            targets = targets[:max_targets]

        if not targets:
            logger.warning("No targets found to validate")
            return {'error': 'No targets found'}

        # Run ingestion
        return self.run(targets, resume=resume)


def main():
    parser = argparse.ArgumentParser(
        description="Validate neuropsych targets with OpenTargets disease associations"
    )
    parser.add_argument(
        '--max-targets',
        type=int,
        default=None,
        help="Maximum number of targets to process (default: all)"
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help="Test mode: process only 5 targets"
    )
    parser.add_argument(
        '--no-resume',
        action='store_true',
        help="Don't resume from checkpoint, start fresh"
    )

    args = parser.parse_args()

    max_targets = 5 if args.test else args.max_targets
    resume = not args.no_resume

    pipeline = NeuropsychOpenTargetsIngestion()
    result = pipeline.run_ingestion(
        max_targets=max_targets,
        resume=resume
    )

    print("\n=== OpenTargets Validation Complete ===")
    print(f"Source: {result.get('source', 'neuropsych_opentargets')}")
    print(f"Total targets: {result.get('total', 0)}")
    print(f"Successful: {result.get('successful', 0)}")
    print(f"Failed: {result.get('failed', 0)}")
    print(f"Duration: {result.get('duration_seconds', 0):.1f}s")

    if result.get('errors'):
        print("\nErrors:")
        for err in result['errors'][:5]:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
