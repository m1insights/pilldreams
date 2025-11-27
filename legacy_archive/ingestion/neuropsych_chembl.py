"""
Neuropsych ChEMBL Binding Data Ingestion

Fetches target and binding affinity data from ChEMBL API for neuropsych drugs.
Writes to the `drugs`, `targets`, and `drug_targets` tables.

Uses IngestionBase for checkpointing, rate limiting, and validation.

Usage:
    python ingestion/neuropsych_chembl.py
    python ingestion/neuropsych_chembl.py --test  # Process only 5 drugs
    python ingestion/neuropsych_chembl.py --resume  # Resume from checkpoint
    python ingestion/neuropsych_chembl.py --drug "fluoxetine"  # Single drug
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


class ChEMBLClient:
    """Client for ChEMBL REST API"""

    BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"

    def __init__(self, rate_limiter):
        """Initialize API client with shared rate limiter."""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "pilldreams/1.0 (neuropsych drug intelligence)",
            "Accept": "application/json"
        })
        self.rate_limiter = rate_limiter

    def search_molecule(self, drug_name: str) -> Optional[str]:
        """
        Search for a molecule by name and return ChEMBL ID.

        Tries:
        1. Exact preferred name match
        2. Contains match
        3. Synonym search

        Args:
            drug_name: Drug name to search

        Returns:
            ChEMBL ID (e.g., "CHEMBL1201585") or None if not found
        """
        self.rate_limiter.wait()

        url = f"{self.BASE_URL}/molecule.json"

        # Try exact preferred name match first
        params = {
            "pref_name__iexact": drug_name,
            "limit": 1
        }

        try:
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if data.get("molecules") and len(data["molecules"]) > 0:
                    chembl_id = data["molecules"][0]["molecule_chembl_id"]
                    logger.debug("Found molecule by exact name", drug=drug_name, chembl_id=chembl_id)
                    return chembl_id

            # Try contains match if exact fails
            self.rate_limiter.wait()
            params = {
                "pref_name__icontains": drug_name,
                "limit": 5
            }

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if data.get("molecules") and len(data["molecules"]) > 0:
                    # Return first match
                    chembl_id = data["molecules"][0]["molecule_chembl_id"]
                    logger.debug("Found molecule by contains", drug=drug_name, chembl_id=chembl_id)
                    return chembl_id

            # Try searching by synonyms
            self.rate_limiter.wait()
            url = f"{self.BASE_URL}/molecule/search.json"
            params = {"q": drug_name}

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if data.get("molecules") and len(data["molecules"]) > 0:
                    chembl_id = data["molecules"][0]["molecule_chembl_id"]
                    logger.debug("Found molecule by search", drug=drug_name, chembl_id=chembl_id)
                    return chembl_id

            logger.debug("No molecule found in ChEMBL", drug=drug_name)
            return None

        except Exception as e:
            logger.error("Failed to search molecule", drug=drug_name, error=str(e))
            return None

    def get_activities(self, chembl_id: str, limit: int = 1000) -> List[Dict]:
        """
        Get binding activity data for a molecule.

        Args:
            chembl_id: ChEMBL molecule ID
            limit: Maximum number of results per page

        Returns:
            List of activity records with target and binding info
        """
        self.rate_limiter.wait()

        url = f"{self.BASE_URL}/activity.json"
        params = {
            "molecule_chembl_id": chembl_id,
            "assay_type": "B",  # Binding assays only
            "limit": limit
        }

        all_activities = []

        try:
            while True:
                response = self.session.get(url, params=params, timeout=30)

                if response.status_code != 200:
                    logger.error(
                        "Failed to get activities",
                        chembl_id=chembl_id,
                        status_code=response.status_code
                    )
                    break

                data = response.json()
                activities = data.get("activities", [])
                all_activities.extend(activities)

                # Check for pagination
                page_meta = data.get("page_meta", {})
                next_url = page_meta.get("next")

                if not next_url:
                    break

                # Update URL for next page
                url = f"https://www.ebi.ac.uk{next_url}"
                params = {}  # Params are in the URL now
                self.rate_limiter.wait()

            logger.debug(
                "Retrieved activities",
                chembl_id=chembl_id,
                count=len(all_activities)
            )
            return all_activities

        except Exception as e:
            logger.error("Failed to get activities", chembl_id=chembl_id, error=str(e))
            return []

    def get_target_info(self, target_chembl_id: str) -> Optional[Dict]:
        """
        Get detailed target information including gene symbol.

        Args:
            target_chembl_id: ChEMBL target ID

        Returns:
            Target info dict or None
        """
        self.rate_limiter.wait()

        url = f"{self.BASE_URL}/target/{target_chembl_id}.json"

        try:
            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return {
                    'chembl_id': target_chembl_id,
                    'name': data.get('pref_name'),
                    'target_type': data.get('target_type'),
                    'organism': data.get('organism'),
                    'target_components': data.get('target_components', [])
                }

            return None

        except Exception as e:
            logger.error("Failed to get target info", target=target_chembl_id, error=str(e))
            return None

    def extract_target_binding_data(self, activities: List[Dict]) -> List[Dict]:
        """
        Extract target and binding affinity data from activity records.

        Args:
            activities: List of activity records from ChEMBL

        Returns:
            List of {target_chembl_id, target_name, target_type, affinity_value, affinity_type, affinity_unit}
        """
        target_data = []

        for activity in activities:
            # Extract target info
            target_chembl_id = activity.get("target_chembl_id")
            target_pref_name = activity.get("target_pref_name")
            target_type = activity.get("target_type")

            # Extract binding affinity
            standard_type = activity.get("standard_type")  # e.g., "Ki", "IC50", "Kd"
            standard_value = activity.get("standard_value")  # Numeric value
            standard_units = activity.get("standard_units")  # e.g., "nM"

            # Extract assay info for context
            assay_description = activity.get("assay_description", "")

            # Only keep records with valid target and binding data
            if not target_chembl_id or not standard_value:
                continue

            # Convert value to float
            try:
                affinity_value = float(standard_value)
            except (ValueError, TypeError):
                continue

            # Filter for relevant binding types (Ki, IC50, Kd, EC50)
            if standard_type not in ["Ki", "IC50", "Kd", "EC50", "Potency"]:
                continue

            target_data.append({
                "target_chembl_id": target_chembl_id,
                "target_name": target_pref_name or "Unknown",
                "target_type": target_type or "Unknown",
                "affinity_value": affinity_value,
                "affinity_type": standard_type,
                "affinity_unit": standard_units or "nM",
                "assay_description": assay_description
            })

        return target_data

    def aggregate_target_affinities(self, target_data: List[Dict]) -> Dict[str, Dict]:
        """
        Aggregate multiple affinity measurements for each target.

        Takes median affinity value when multiple measurements exist.

        Args:
            target_data: List of target-binding records

        Returns:
            Dict of {target_chembl_id: {target_name, target_type, median_affinity, affinity_type, count}}
        """
        # Group by target
        target_groups = defaultdict(lambda: {
            "affinities": [],
            "target_name": None,
            "target_type": None,
            "affinity_types": []
        })

        for record in target_data:
            target_id = record["target_chembl_id"]
            target_groups[target_id]["affinities"].append(record["affinity_value"])
            target_groups[target_id]["affinity_types"].append(record["affinity_type"])

            if not target_groups[target_id]["target_name"]:
                target_groups[target_id]["target_name"] = record["target_name"]
                target_groups[target_id]["target_type"] = record["target_type"]

        # Calculate median affinity for each target
        aggregated = {}
        for target_id, data in target_groups.items():
            affinities = sorted(data["affinities"])
            n = len(affinities)

            if n == 0:
                continue

            # Median
            if n % 2 == 0:
                median_affinity = (affinities[n//2 - 1] + affinities[n//2]) / 2
            else:
                median_affinity = affinities[n//2]

            # Most common affinity type
            affinity_type_counts = {}
            for aff_type in data["affinity_types"]:
                affinity_type_counts[aff_type] = affinity_type_counts.get(aff_type, 0) + 1
            most_common_type = max(affinity_type_counts.items(), key=lambda x: x[1])[0]

            aggregated[target_id] = {
                "target_chembl_id": target_id,
                "target_name": data["target_name"],
                "target_type": data["target_type"],
                "median_affinity": round(median_affinity, 2),
                "affinity_type": most_common_type,
                "measurement_count": n
            }

        return aggregated


class NeuropsychChEMBLIngestion(IngestionBase):
    """
    ChEMBL binding data ingestion for neuropsych drugs.

    Reads from `drugs` table, writes to `drug_targets` and `targets`.
    """

    def __init__(self):
        super().__init__(
            source_name='neuropsych_chembl',
            rate_limit=5.0  # 5 requests/second
        )
        self.api = ChEMBLClient(self.rate_limiter)

    def get_neuropsych_drugs(self) -> List[Dict[str, Any]]:
        """
        Fetch all drugs from the neuropsych-focused `drugs` table.

        Returns:
            List of drug records with id, name, chembl_id
        """
        drugs = []
        page_size = 1000
        offset = 0

        while True:
            response = self.db.client.table('drugs').select(
                'id, name, chembl_id, tier'
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
        Fetch ChEMBL binding data for a drug.

        Args:
            item: Drug record with name and optional chembl_id

        Returns:
            Dict with chembl_id and aggregated binding data
        """
        drug_name = item['name']
        existing_chembl_id = item.get('chembl_id')

        # Normalize drug name for API query
        normalized_name = self.normalize_drug_name(drug_name)

        # Get ChEMBL ID
        if existing_chembl_id:
            chembl_id = existing_chembl_id
        else:
            chembl_id = self.api.search_molecule(normalized_name)

            if not chembl_id:
                logger.debug("No ChEMBL ID found", drug=drug_name, normalized=normalized_name)
                return None

        # Get binding activities
        activities = self.api.get_activities(chembl_id)

        if not activities:
            logger.debug("No activities found", drug=drug_name, chembl_id=chembl_id)
            return {'chembl_id': chembl_id, 'binding_data': {}}

        # Extract and aggregate target data
        target_data = self.api.extract_target_binding_data(activities)
        aggregated = self.api.aggregate_target_affinities(target_data)

        return {
            'chembl_id': chembl_id,
            'binding_data': aggregated
        }

    def process_item(self, item: Dict[str, Any]) -> Tuple[bool, int, int]:
        """
        Process a single drug - fetch ChEMBL data and store binding info.

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
            # Fetch ChEMBL data
            data = self.fetch_data(item)

            if not data:
                return (True, 0, 0)  # No data is not a failure

            chembl_id = data['chembl_id']
            binding_data = data['binding_data']

            # Update drug with ChEMBL ID if not already set
            if chembl_id and not item.get('chembl_id'):
                self.db.client.table('drugs').update({
                    'chembl_id': chembl_id,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', drug_id).execute()
                records_updated += 1

            # Skip if no binding data
            if not binding_data:
                return (True, records_created, records_updated)

            # Process each target binding
            for target_chembl_id, binding_info in binding_data.items():
                try:
                    # Get or create target
                    target_id = self._get_or_create_target(
                        target_chembl_id,
                        binding_info
                    )

                    if not target_id:
                        continue

                    # Check if drug-target binding exists
                    existing_binding = self.db.client.table('drug_targets').select('id').eq(
                        'drug_id', drug_id
                    ).eq('target_id', target_id).execute()

                    now = datetime.now().isoformat()

                    # Calculate confidence score from measurement count (more measurements = higher confidence)
                    # Scale: 1 measurement = 0.3, 5 = 0.6, 10+ = 0.9
                    measurement_count = binding_info['measurement_count']
                    confidence = min(0.9, 0.3 + (measurement_count - 1) * 0.1)

                    if existing_binding.data:
                        # Update existing binding
                        self.db.client.table('drug_targets').update({
                            'affinity_value': binding_info['median_affinity'],
                            'affinity_type': binding_info['affinity_type'],
                            'confidence_score': round(confidence, 2)
                        }).eq('id', existing_binding.data[0]['id']).execute()
                        records_updated += 1
                    else:
                        # Insert new binding
                        self.db.client.table('drug_targets').insert({
                            'drug_id': drug_id,
                            'target_id': target_id,
                            'affinity_value': binding_info['median_affinity'],
                            'affinity_type': binding_info['affinity_type'],
                            'affinity_unit': 'nM',
                            'confidence_score': round(confidence, 2),
                            'created_at': now
                        }).execute()
                        records_created += 1

                except Exception as e:
                    logger.error(
                        "Failed to insert binding",
                        drug=drug_name,
                        target=target_chembl_id,
                        error=str(e)
                    )

            return (True, records_created, records_updated)

        except Exception as e:
            logger.error("Failed to process drug", drug=drug_name, error=str(e))
            return (False, records_created, records_updated)

    def _get_or_create_target(
        self,
        target_chembl_id: str,
        binding_info: Dict[str, Any]
    ) -> Optional[str]:
        """
        Get existing target or create new one.

        Args:
            target_chembl_id: ChEMBL target ID
            binding_info: Binding data with target name and type

        Returns:
            Target ID (UUID) or None
        """
        try:
            # Check if target exists by ChEMBL ID (column is 'chembl_id' not 'chembl_target_id')
            existing = self.db.client.table('targets').select('id').eq(
                'chembl_id', target_chembl_id
            ).execute()

            if existing.data:
                return existing.data[0]['id']

            # Also check by symbol (target name) for neuropsych seed targets
            target_symbol = binding_info['target_name'][:100]  # Truncate to fit
            existing_by_symbol = self.db.client.table('targets').select('id').eq(
                'symbol', target_symbol
            ).execute()

            if existing_by_symbol.data:
                # Update with ChEMBL ID
                self.db.client.table('targets').update({
                    'chembl_id': target_chembl_id
                }).eq('id', existing_by_symbol.data[0]['id']).execute()
                return existing_by_symbol.data[0]['id']

            # Get additional target info from ChEMBL
            target_info = self.api.get_target_info(target_chembl_id)

            # Extract gene symbol if available
            gene_symbol = None
            uniprot_id = None
            if target_info and target_info.get('target_components'):
                for component in target_info['target_components']:
                    accession = component.get('accession')
                    if accession:
                        uniprot_id = accession
                    # Check for gene symbol in target synonyms
                    for synonym in component.get('target_component_synonyms', []):
                        if synonym.get('syn_type') == 'GENE_SYMBOL':
                            gene_symbol = synonym.get('component_synonym')
                            break

            # Use gene symbol if found, otherwise use target name
            symbol = gene_symbol or target_symbol

            # Insert new target
            now = datetime.now().isoformat()
            new_target = self.db.client.table('targets').insert({
                'symbol': symbol,
                'chembl_id': target_chembl_id,
                'description': binding_info['target_name'],
                'uniprot_id': uniprot_id,
                'created_at': now
            }).execute()

            if new_target.data:
                logger.debug("Created target", symbol=symbol, chembl_id=target_chembl_id)
                return new_target.data[0]['id']

            return None

        except Exception as e:
            logger.error("Failed to get/create target", target=target_chembl_id, error=str(e))
            return None

    def run_ingestion(
        self,
        max_drugs: Optional[int] = None,
        single_drug: Optional[str] = None,
        resume: bool = True
    ) -> Dict[str, Any]:
        """
        Run the ChEMBL binding data ingestion.

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
                'id, name, chembl_id, tier'
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
        description="Ingest ChEMBL binding data for neuropsych drugs"
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

    pipeline = NeuropsychChEMBLIngestion()
    result = pipeline.run_ingestion(
        max_drugs=max_drugs,
        single_drug=args.drug,
        resume=resume
    )

    print("\n=== Ingestion Complete ===")
    print(f"Source: {result.get('source', 'neuropsych_chembl')}")
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
