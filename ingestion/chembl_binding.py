"""
ChEMBL Binding Data Ingestion Script

Fetches target and binding affinity data from ChEMBL API for mechanism of action analysis.

API Documentation: https://chembl.gitbook.io/chembl-interface-documentation/web-services
"""

import os
import sys
import requests
import time
from typing import Dict, List, Optional, Tuple
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


class ChEMBLClient:
    """Client for ChEMBL REST API"""

    BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"

    # Conservative rate limiting (no official limits, but be respectful)
    REQUESTS_PER_SECOND = 5
    RATE_LIMIT_DELAY = 1.0 / REQUESTS_PER_SECOND  # 0.2 seconds

    def __init__(self):
        """Initialize API client"""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "pilldreams/1.0 (drug intelligence platform)",
            "Accept": "application/json"
        })
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()

    def search_molecule(self, drug_name: str) -> Optional[str]:
        """
        Search for a molecule by name and return ChEMBL ID.

        Args:
            drug_name: Drug name to search

        Returns:
            ChEMBL ID (e.g., "CHEMBL1201585") or None if not found
        """
        self._rate_limit()

        # Try exact preferred name match first
        url = f"{self.BASE_URL}/molecule.json"
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
            self._rate_limit()
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

            logger.debug("No molecule found in ChEMBL", drug=drug_name)
            return None

        except Exception as e:
            logger.error("Failed to search molecule", drug=drug_name, error=str(e))
            return None

    def get_activities(
        self,
        chembl_id: str,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Get binding activity data for a molecule.

        Args:
            chembl_id: ChEMBL molecule ID
            limit: Maximum number of results per page

        Returns:
            List of activity records with target and binding info
        """
        self._rate_limit()

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
                self._rate_limit()

            logger.debug(
                "Retrieved activities",
                chembl_id=chembl_id,
                count=len(all_activities)
            )
            return all_activities

        except Exception as e:
            logger.error("Failed to get activities", chembl_id=chembl_id, error=str(e))
            return []

    def extract_target_binding_data(
        self,
        activities: List[Dict]
    ) -> List[Dict]:
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

    def aggregate_target_affinities(
        self,
        target_data: List[Dict]
    ) -> Dict[str, Dict]:
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


class ChEMBLIngestionPipeline:
    """Pipeline for ingesting ChEMBL binding data into Supabase"""

    def __init__(self):
        """Initialize pipeline"""
        self.api = ChEMBLClient()
        self.db = get_client()

    def ingest_binding_data(self, max_drugs: Optional[int] = None):
        """
        Main ingestion pipeline.

        Args:
            max_drugs: Maximum number of drugs to process (None = all)
        """
        logger.info("Starting ChEMBL binding data ingestion", max_drugs=max_drugs or "all")

        # Step 1: Fetch all drugs from database with pagination
        # Supabase has a default limit of 1000, need to paginate through all
        drugs = []
        page_size = 1000
        offset = 0

        while True:
            drugs_response = self.db.client.table('drug').select('id, name').range(offset, offset + page_size - 1).execute()
            if not drugs_response.data:
                break
            drugs.extend(drugs_response.data)
            logger.info(f"Fetched drugs batch", offset=offset, count=len(drugs_response.data), total_so_far=len(drugs))

            if len(drugs_response.data) < page_size:
                break  # Last page
            offset += page_size

            if max_drugs and len(drugs) >= max_drugs:
                drugs = drugs[:max_drugs]
                break

        if not drugs:
            logger.warning("No drugs found in database")
            return

        logger.info("Fetched all drugs from database", total_count=len(drugs))

        # Step 2: For each drug, fetch ChEMBL data
        total_drugs_processed = 0
        total_targets_inserted = 0
        total_bindings_inserted = 0
        drugs_with_data = 0

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

            # Search for molecule in ChEMBL using normalized name
            chembl_id = self.api.search_molecule(normalized_name)

            if not chembl_id:
                logger.debug("No ChEMBL ID found", drug=drug_name)
                continue

            # Update drug record with ChEMBL ID
            try:
                self.db.client.table("drug").update({
                    "chembl_id": chembl_id
                }).eq("id", drug_id).execute()
            except Exception as e:
                logger.error("Failed to update ChEMBL ID", drug=drug_name, error=str(e))

            # Get binding activities
            activities = self.api.get_activities(chembl_id)

            if not activities:
                logger.debug("No activities found", drug=drug_name, chembl_id=chembl_id)
                continue

            # Extract and aggregate target data
            target_data = self.api.extract_target_binding_data(activities)
            aggregated = self.api.aggregate_target_affinities(target_data)

            if not aggregated:
                logger.debug("No valid binding data", drug=drug_name)
                continue

            drugs_with_data += 1

            # Step 3: Insert targets and bindings
            for target_chembl_id, binding_data in aggregated.items():
                try:
                    # Check if target exists
                    existing_target = self.db.client.table("target").select("id").eq(
                        "target_chembl_id", target_chembl_id
                    ).execute()

                    if existing_target.data:
                        target_id = existing_target.data[0]["id"]
                    else:
                        # Insert new target
                        # Use target name as symbol (required field) if no gene symbol available
                        target_symbol = binding_data["target_name"][:100]  # Truncate to fit VARCHAR(100)

                        new_target = self.db.client.table("target").insert({
                            "target_chembl_id": target_chembl_id,
                            "symbol": target_symbol,
                            "name": binding_data["target_name"],
                            "target_type": binding_data["target_type"]
                        }).execute()
                        target_id = new_target.data[0]["id"]
                        total_targets_inserted += 1
                        logger.debug("Inserted target", target=binding_data["target_name"])

                    # Check if drug-target binding exists
                    existing_binding = self.db.client.table("drugtarget").select("id").eq(
                        "drug_id", drug_id
                    ).eq("target_id", target_id).execute()

                    if existing_binding.data:
                        # Update existing binding
                        self.db.client.table("drugtarget").update({
                            "affinity_value": binding_data["median_affinity"],
                            "affinity_type": binding_data["affinity_type"],
                            "measurement_count": binding_data["measurement_count"]
                        }).eq("id", existing_binding.data[0]["id"]).execute()
                        logger.debug("Updated binding", drug=drug_name, target=binding_data["target_name"])
                    else:
                        # Insert new binding
                        self.db.client.table("drugtarget").insert({
                            "drug_id": drug_id,
                            "target_id": target_id,
                            "affinity_value": binding_data["median_affinity"],
                            "affinity_type": binding_data["affinity_type"],
                            "measurement_count": binding_data["measurement_count"]
                        }).execute()
                        total_bindings_inserted += 1
                        logger.debug("Inserted binding", drug=drug_name, target=binding_data["target_name"])

                except Exception as e:
                    logger.error(
                        "Failed to insert target/binding",
                        drug=drug_name,
                        target=target_chembl_id,
                        error=str(e)
                    )

            total_drugs_processed += 1

        logger.info(
            "ChEMBL binding data ingestion complete",
            drugs_processed=total_drugs_processed,
            drugs_with_data=drugs_with_data,
            targets_inserted=total_targets_inserted,
            bindings_inserted=total_bindings_inserted
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest binding data from ChEMBL")
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

    pipeline = ChEMBLIngestionPipeline()
    pipeline.ingest_binding_data(max_drugs=max_drugs)
