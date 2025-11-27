"""
Neuropsych UniProt Target Enrichment

Enriches targets in the database with protein function, subcellular location,
and pathway information from UniProt REST API.

Uses IngestionBase for rate limiting and structured logging.

Usage:
    python ingestion/neuropsych_uniprot.py
    python ingestion/neuropsych_uniprot.py --test  # Process only 5 targets
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


class UniProtClient:
    """Client for UniProt REST API"""

    BASE_URL = "https://rest.uniprot.org/uniprotkb"

    def __init__(self, rate_limiter):
        """
        Initialize API client.

        Args:
            rate_limiter: Shared rate limiter
        """
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "pilldreams/1.0 (neuropsych drug intelligence)",
            "Accept": "application/json"
        })
        self.rate_limiter = rate_limiter

    def get_protein_data(self, uniprot_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed protein data from UniProt.

        Args:
            uniprot_id: UniProt accession ID (e.g., P08908)

        Returns:
            Protein data dict or None if not found
        """
        self.rate_limiter.wait()

        url = f"{self.BASE_URL}/{uniprot_id}.json"

        try:
            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.debug("UniProt entry not found", uniprot_id=uniprot_id)
                return None
            else:
                logger.error(
                    "UniProt API error",
                    uniprot_id=uniprot_id,
                    status_code=response.status_code
                )
                return None

        except Exception as e:
            logger.error("Failed to fetch UniProt data", uniprot_id=uniprot_id, error=str(e))
            return None

    def search_by_gene_symbol(self, symbol: str, organism: str = "9606") -> Optional[str]:
        """
        Search for UniProt ID by gene symbol.

        Args:
            symbol: Gene symbol (e.g., HTR1A)
            organism: Taxonomy ID (9606 = human)

        Returns:
            UniProt accession ID or None
        """
        self.rate_limiter.wait()

        # Search query: gene symbol + human organism
        query = f"gene_exact:{symbol} AND organism_id:{organism}"
        url = f"{self.BASE_URL}/search"

        params = {
            "query": query,
            "format": "json",
            "size": 1,
            "fields": "accession,gene_names,protein_name"
        }

        try:
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results:
                    return results[0].get("primaryAccession")
            return None

        except Exception as e:
            logger.error("Failed to search UniProt", symbol=symbol, error=str(e))
            return None

    def extract_function(self, data: Dict[str, Any]) -> str:
        """Extract protein function description from UniProt data."""
        comments = data.get("comments", [])
        for comment in comments:
            if comment.get("commentType") == "FUNCTION":
                texts = comment.get("texts", [])
                if texts:
                    return texts[0].get("value", "")
        return ""

    def extract_subcellular_location(self, data: Dict[str, Any]) -> List[str]:
        """Extract subcellular locations from UniProt data."""
        locations = []
        comments = data.get("comments", [])
        for comment in comments:
            if comment.get("commentType") == "SUBCELLULAR LOCATION":
                for loc in comment.get("subcellularLocations", []):
                    location_data = loc.get("location", {})
                    val = location_data.get("value")
                    if val:
                        locations.append(val)
        return locations

    def extract_pathway(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Extract pathway information from UniProt data.

        Looks at:
        1. Pathway comments
        2. Keywords related to signaling
        3. GO terms for biological process
        """
        # Check pathway comments
        comments = data.get("comments", [])
        for comment in comments:
            if comment.get("commentType") == "PATHWAY":
                texts = comment.get("texts", [])
                if texts:
                    return texts[0].get("value", "")

        # Check keywords for pathway hints
        keywords = data.get("keywords", [])
        pathway_keywords = []
        pathway_terms = [
            "Receptor", "Signal transduction", "G-protein coupled",
            "Neurotransmitter", "Ion channel", "Kinase", "Phosphatase"
        ]

        for kw in keywords:
            name = kw.get("name", "")
            if any(term.lower() in name.lower() for term in pathway_terms):
                pathway_keywords.append(name)

        if pathway_keywords:
            return "; ".join(pathway_keywords[:3])  # Return top 3

        return None

    def extract_go_terms(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Extract GO terms organized by aspect.

        Returns:
            Dict with keys: molecular_function, biological_process, cellular_component
        """
        go_terms = {
            "molecular_function": [],
            "biological_process": [],
            "cellular_component": []
        }

        # GO terms are in uniProtKBCrossReferences
        cross_refs = data.get("uniProtKBCrossReferences", [])

        for ref in cross_refs:
            if ref.get("database") == "GO":
                go_id = ref.get("id", "")
                properties = ref.get("properties", [])

                for prop in properties:
                    if prop.get("key") == "GoTerm":
                        term = prop.get("value", "")

                        # Categorize by GO aspect prefix
                        if term.startswith("F:"):
                            go_terms["molecular_function"].append(term[2:])
                        elif term.startswith("P:"):
                            go_terms["biological_process"].append(term[2:])
                        elif term.startswith("C:"):
                            go_terms["cellular_component"].append(term[2:])

        return go_terms


class NeuropsychUniProtIngestion(IngestionBase):
    """
    UniProt enrichment for neuropsych targets.

    Reads from `targets` table, enriches with UniProt data.
    """

    def __init__(self):
        super().__init__(
            source_name='neuropsych_uniprot',
            rate_limit=5.0  # 5 requests/second
        )
        self.api = UniProtClient(self.rate_limiter)

    def get_targets_to_enrich(self) -> List[Dict[str, Any]]:
        """
        Fetch targets that need UniProt enrichment.

        Prioritizes targets without descriptions.
        """
        targets = []
        page_size = 1000
        offset = 0

        while True:
            # Get targets - prioritize those without descriptions
            response = self.db.client.table('targets').select(
                'id, symbol, uniprot_id, description, pathway'
            ).range(offset, offset + page_size - 1).execute()

            if not response.data:
                break

            targets.extend(response.data)

            if len(response.data) < page_size:
                break

            offset += page_size

        logger.info("Fetched targets for enrichment", count=len(targets))
        return targets

    def fetch_data(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fetch UniProt data for a target.

        Args:
            item: Target record with symbol and optional uniprot_id

        Returns:
            Enrichment data dict or None
        """
        symbol = item['symbol']
        uniprot_id = item.get('uniprot_id')

        # Try to get UniProt ID if not present
        if not uniprot_id:
            uniprot_id = self.api.search_by_gene_symbol(symbol)
            if not uniprot_id:
                logger.debug("No UniProt ID found", symbol=symbol)
                return None

        # Fetch full protein data
        protein_data = self.api.get_protein_data(uniprot_id)
        if not protein_data:
            return None

        # Extract relevant fields
        function_desc = self.api.extract_function(protein_data)
        locations = self.api.extract_subcellular_location(protein_data)
        pathway = self.api.extract_pathway(protein_data)
        go_terms = self.api.extract_go_terms(protein_data)

        return {
            'uniprot_id': uniprot_id,
            'description': function_desc,
            'subcellular_locations': locations,
            'pathway': pathway,
            'go_terms': go_terms
        }

    def process_item(self, item: Dict[str, Any]) -> Tuple[bool, int, int]:
        """
        Process a single target - fetch UniProt data and update.

        Args:
            item: Target record from `targets` table

        Returns:
            (success, records_created, records_updated)
        """
        target_id = item['id']
        symbol = item['symbol']

        try:
            # Fetch UniProt data
            data = self.fetch_data(item)

            if not data:
                # No data found - not a failure, just no update
                return (True, 0, 0)

            # Prepare update
            update_data = {}

            # Update uniprot_id if found
            if data.get('uniprot_id') and not item.get('uniprot_id'):
                update_data['uniprot_id'] = data['uniprot_id']

            # Update description if we have a better one
            if data.get('description'):
                # Truncate to 500 chars if needed
                desc = data['description']
                if len(desc) > 500:
                    desc = desc[:497] + "..."
                update_data['description'] = desc

            # Update pathway if found and not already set
            if data.get('pathway') and not item.get('pathway'):
                update_data['pathway'] = data['pathway']

            # Only update if we have something to update
            if not update_data:
                return (True, 0, 0)

            # Perform update
            self.db.client.table('targets').update(
                update_data
            ).eq('id', target_id).execute()

            logger.debug(
                "Enriched target",
                symbol=symbol,
                fields_updated=list(update_data.keys())
            )

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
        Run the UniProt enrichment.

        Args:
            max_targets: Maximum number of targets to process
            resume: Resume from checkpoint

        Returns:
            Summary dict with counts
        """
        # Get targets to enrich
        targets = self.get_targets_to_enrich()

        if max_targets:
            targets = targets[:max_targets]

        if not targets:
            logger.warning("No targets found to enrich")
            return {'error': 'No targets found'}

        # Run ingestion
        return self.run(targets, resume=resume)


def main():
    parser = argparse.ArgumentParser(
        description="Enrich neuropsych targets with UniProt data"
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

    pipeline = NeuropsychUniProtIngestion()
    result = pipeline.run_ingestion(
        max_targets=max_targets,
        resume=resume
    )

    print("\n=== UniProt Enrichment Complete ===")
    print(f"Source: {result.get('source', 'neuropsych_uniprot')}")
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
