"""
ClinicalTrials.gov Ingestion Script

Fetches active clinical trials (Phase 1-3) and extracts compounds for investor analysis.

API Documentation: https://clinicaltrials.gov/data-api/api
"""

import os
import sys
import requests
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import structlog
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.supabase_client import get_client

load_dotenv()
logger = structlog.get_logger()


class ClinicalTrialsAPI:
    """Client for ClinicalTrials.gov API v2"""

    BASE_URL = "https://clinicaltrials.gov/api/v2"

    def __init__(self):
        """Initialize API client"""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "pilldreams/1.0 (research tool for drug intelligence)"
        })

    def search_trials(
        self,
        phase: Optional[List[str]] = None,
        status: Optional[List[str]] = None,
        page_size: int = 1000,
        max_results: Optional[int] = None
    ) -> List[Dict]:
        """
        Search for clinical trials.

        Args:
            phase: List of phases to include (e.g., ["PHASE1", "PHASE2", "PHASE3"])
            status: List of statuses (e.g., ["RECRUITING", "ACTIVE_NOT_RECRUITING"])
            page_size: Number of results per page (max 1000)
            max_results: Maximum total results to fetch (None = all)

        Returns:
            List of trial dictionaries
        """
        all_trials = []
        next_page_token = None

        # Default to investor-relevant phases and statuses
        if phase is None:
            phase = ["PHASE1", "PHASE2", "PHASE3"]

        if status is None:
            status = [
                "RECRUITING",
                "ACTIVE_NOT_RECRUITING",
                "ENROLLING_BY_INVITATION",
                "NOT_YET_RECRUITING"
            ]

        logger.info(
            "Searching ClinicalTrials.gov",
            phases=phase,
            statuses=status,
            max_results=max_results or "unlimited"
        )

        while True:
            # Build query parameters (API v2 format)
            # Docs: https://clinicaltrials.gov/data-api/api
            params = {
                "format": "json",
                "pageSize": page_size,
            }

            # Build query string for phases and statuses
            query_parts = []

            if phase:
                # Phase filter in query
                phase_query = " OR ".join([f"AREA[Phase]{p}" for p in phase])
                query_parts.append(f"({phase_query})")

            if status:
                # Status filter in query
                status_query = " OR ".join([f'AREA[OverallStatus]"{s}"' for s in status])
                query_parts.append(f"({status_query})")

            if query_parts:
                params["query.cond"] = " AND ".join(query_parts)

            if next_page_token:
                params["pageToken"] = next_page_token

            # Make request
            try:
                response = self.session.get(
                    f"{self.BASE_URL}/studies",
                    params=params,
                    timeout=30
                )

                # Check for errors before raising
                if response.status_code != 200:
                    logger.error(
                        "API error",
                        status_code=response.status_code,
                        response=response.text[:500]
                    )
                    break

                data = response.json()

                # Extract trials
                studies = data.get("studies", [])
                all_trials.extend(studies)

                logger.info(
                    "Fetched trials page",
                    count=len(studies),
                    total_so_far=len(all_trials)
                )

                # Check if we should continue
                next_page_token = data.get("nextPageToken")

                if not next_page_token:
                    break

                if max_results and len(all_trials) >= max_results:
                    all_trials = all_trials[:max_results]
                    break

                # Rate limiting - be respectful
                time.sleep(0.5)

            except Exception as e:
                logger.error("Failed to fetch trials", error=str(e))
                break

        logger.info("Trial search complete", total_trials=len(all_trials))
        return all_trials

    def extract_interventions(self, trial: Dict) -> List[Dict]:
        """
        Extract drug/intervention information from a trial.

        Args:
            trial: Trial dictionary from API

        Returns:
            List of intervention dicts with name and type
        """
        interventions = []

        protocol_section = trial.get("protocolSection", {})
        arms_interventions = protocol_section.get("armsInterventionsModule", {})

        for intervention in arms_interventions.get("interventions", []):
            intervention_type = intervention.get("type", "").upper()

            # Only include drug-like interventions (investor-relevant)
            if intervention_type in ["DRUG", "BIOLOGICAL", "GENETIC", "DIETARY_SUPPLEMENT"]:
                interventions.append({
                    "name": intervention.get("name", "").strip(),
                    "type": intervention_type,
                    "description": intervention.get("description", "")
                })

        return interventions


class TrialIngestionPipeline:
    """Pipeline for ingesting trials into Supabase"""

    def __init__(self):
        """Initialize pipeline"""
        self.api = ClinicalTrialsAPI()
        self.db = get_client()

    def normalize_compound_name(self, name: str) -> str:
        """
        Normalize compound name for consistency.

        Args:
            name: Raw compound name

        Returns:
            Normalized name
        """
        # Remove common prefixes/suffixes
        name = name.strip()

        # Remove dosage info
        name = name.split(" mg")[0]
        name = name.split(" mcg")[0]
        name = name.split(" g")[0]

        # Remove parenthetical info (keep base name)
        if "(" in name:
            name = name.split("(")[0].strip()

        return name

    def normalize_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        Normalize date string to PostgreSQL-compatible format.

        Args:
            date_str: Date string (may be YYYY, YYYY-MM, or YYYY-MM-DD)

        Returns:
            Date in YYYY-MM-DD format or None
        """
        if not date_str:
            return None

        # Handle different date formats
        parts = date_str.split("-")

        if len(parts) == 1:
            # YYYY -> YYYY-01-01
            return f"{parts[0]}-01-01"
        elif len(parts) == 2:
            # YYYY-MM -> YYYY-MM-01
            return f"{date_str}-01"
        else:
            # Already YYYY-MM-DD
            return date_str

    def extract_trial_metadata(self, trial: Dict) -> Dict:
        """
        Extract key trial metadata.

        Args:
            trial: Raw trial dict from API

        Returns:
            Normalized trial metadata
        """
        protocol = trial.get("protocolSection", {})
        id_module = protocol.get("identificationModule", {})
        design_module = protocol.get("designModule", {})
        status_module = protocol.get("statusModule", {})
        sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
        conditions_module = protocol.get("conditionsModule", {})
        outcomes_module = protocol.get("outcomesModule", {})

        # Extract NCT ID
        nct_id = id_module.get("nctId", "")

        # Extract phase
        phases = design_module.get("phases", [])
        phase = phases[0] if phases else "UNKNOWN"
        phase = phase.replace("PHASE", "").strip()  # "PHASE2" -> "2"

        # Extract status
        status = status_module.get("overallStatus", "UNKNOWN")

        # Extract sponsor type
        lead_sponsor = sponsor_module.get("leadSponsor", {})
        sponsor_type = lead_sponsor.get("class", "UNKNOWN")

        # Extract condition
        conditions = conditions_module.get("conditions", [])
        condition = conditions[0] if conditions else "Unknown"

        # Extract enrollment
        design_info = design_module.get("enrollmentInfo", {})
        enrollment = design_info.get("count", 0)

        # Extract dates (normalize to YYYY-MM-DD format)
        start_date = self.normalize_date(status_module.get("startDateStruct", {}).get("date"))
        primary_completion_date = self.normalize_date(status_module.get("primaryCompletionDateStruct", {}).get("date"))
        completion_date = self.normalize_date(status_module.get("completionDateStruct", {}).get("date"))

        # Extract primary endpoint
        primary_outcomes = outcomes_module.get("primaryOutcomes", [])
        primary_endpoint = primary_outcomes[0].get("measure", "") if primary_outcomes else ""

        # Extract design features
        design_info = design_module.get("designInfo", {})
        allocation = design_info.get("allocation", "")
        intervention_model = design_info.get("interventionModel", "")
        masking = design_info.get("maskingInfo", {}).get("masking", "")

        has_placebo_arm = "PLACEBO" in intervention_model.upper() or allocation == "RANDOMIZED"
        has_active_comparator = "ACTIVE_COMPARATOR" in intervention_model.upper()
        is_randomized = allocation == "RANDOMIZED"
        is_blinded = masking in ["DOUBLE", "TRIPLE", "QUADRUPLE"]

        return {
            "nct_id": nct_id,
            "phase": phase,
            "status": status,
            "condition": condition,
            "sponsor_type": sponsor_type,
            "enrollment": enrollment,
            "start_date": start_date,
            "primary_completion_date": primary_completion_date,
            "completion_date": completion_date,
            "primary_endpoint": primary_endpoint,
            "has_placebo_arm": has_placebo_arm,
            "has_active_comparator": has_active_comparator,
            "is_randomized": is_randomized,
            "is_blinded": is_blinded
        }

    def ingest_trials(self, max_trials: Optional[int] = None):
        """
        Main ingestion pipeline.

        Args:
            max_trials: Maximum number of trials to ingest (None = all)
        """
        logger.info("Starting trial ingestion pipeline", max_trials=max_trials or "unlimited")

        # Step 1: Fetch trials from ClinicalTrials.gov
        trials = self.api.search_trials(max_results=max_trials)

        if not trials:
            logger.warning("No trials found")
            return

        # Step 2: Extract unique compounds
        compound_map = {}  # name -> metadata
        trial_interventions = {}  # nct_id -> [compound_names]

        for trial in trials:
            nct_id = trial.get("protocolSection", {}).get("identificationModule", {}).get("nctId", "")
            interventions = self.api.extract_interventions(trial)

            trial_interventions[nct_id] = []

            for intervention in interventions:
                raw_name = intervention["name"]
                normalized_name = self.normalize_compound_name(raw_name)

                if normalized_name and len(normalized_name) > 2:  # Filter out junk
                    compound_map[normalized_name] = {
                        "name": normalized_name,
                        "is_approved": False,  # Pipeline drugs
                        "class": None  # Will be enriched later
                    }
                    trial_interventions[nct_id].append(normalized_name)

        logger.info(
            "Extracted unique compounds",
            total_compounds=len(compound_map),
            total_trials=len(trials)
        )

        # Step 3: Insert compounds into Drug table (skip duplicates)
        logger.info("Inserting compounds into Drug table...")

        compound_ids = {}  # name -> UUID

        for compound_name, compound_data in compound_map.items():
            try:
                # Check if exists (table names are lowercase in PostgreSQL)
                existing = self.db.client.table("drug").select("id").eq("name", compound_name).execute()

                if existing.data:
                    compound_ids[compound_name] = existing.data[0]["id"]
                    logger.debug("Compound already exists", name=compound_name)
                else:
                    # Insert new
                    result = self.db.client.table("drug").insert(compound_data).execute()
                    compound_ids[compound_name] = result.data[0]["id"]
                    logger.debug("Inserted compound", name=compound_name)

            except Exception as e:
                logger.error("Failed to insert compound", name=compound_name, error=str(e))

        logger.info("Compound insertion complete", total_inserted=len(compound_ids))

        # Step 4: Insert trials into Trial table
        logger.info("Inserting trials into Trial table...")

        trials_inserted = 0
        interventions_inserted = 0

        for trial in trials:
            try:
                # Extract metadata
                trial_metadata = self.extract_trial_metadata(trial)
                nct_id = trial_metadata["nct_id"]

                # Find all compounds for this trial
                compound_names = trial_interventions.get(nct_id, [])

                if not compound_names:
                    continue

                # Use first compound as primary (for backwards compatibility)
                primary_compound = compound_names[0]
                drug_id = compound_ids.get(primary_compound)

                if not drug_id:
                    continue

                # Add drug_id to metadata
                trial_metadata["drug_id"] = drug_id

                # Insert trial (skip if exists) - lowercase table name
                existing = self.db.client.table("trial").select("nct_id").eq("nct_id", nct_id).execute()

                if not existing.data:
                    self.db.client.table("trial").insert(trial_metadata).execute()
                    trials_inserted += 1
                    logger.debug("Inserted trial", nct_id=nct_id)

                # NEW: Insert ALL compounds into junction table (many-to-many)
                for compound_name in compound_names:
                    compound_id = compound_ids.get(compound_name)
                    if not compound_id:
                        continue

                    try:
                        # Check if intervention link exists
                        existing_link = self.db.client.table("trial_intervention").select("id").eq("trial_id", nct_id).eq("drug_id", compound_id).execute()

                        if not existing_link.data:
                            # Insert intervention link
                            self.db.client.table("trial_intervention").insert({
                                "trial_id": nct_id,
                                "drug_id": compound_id,
                                "intervention_role": "experimental" if compound_name == primary_compound else "other"
                            }).execute()
                            interventions_inserted += 1
                            logger.debug("Linked intervention", nct_id=nct_id, drug=compound_name)

                    except Exception as e:
                        logger.error("Failed to insert intervention link", nct_id=nct_id, drug=compound_name, error=str(e))

            except Exception as e:
                logger.error("Failed to insert trial", nct_id=nct_id, error=str(e))

        logger.info(
            "Trial ingestion complete",
            trials_inserted=trials_inserted,
            compounds_inserted=len(compound_ids),
            interventions_linked=interventions_inserted
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest clinical trials from ClinicalTrials.gov")
    parser.add_argument(
        "--max-trials",
        type=int,
        default=None,
        help="Maximum number of trials to fetch (default: all)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: fetch only 10 trials"
    )

    args = parser.parse_args()

    max_trials = 10 if args.test else args.max_trials

    pipeline = TrialIngestionPipeline()
    pipeline.ingest_trials(max_trials=max_trials)
