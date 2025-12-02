"""
ETL 32: Fetch Clinical Trial Dates from ClinicalTrials.gov API v2

Surgical query strategy to avoid polluting with irrelevant trials:

TIER 1 (Curated): For PCSK9, TTR, E2F drugs - only fetch specific NCT IDs
    from ci_curated_trials table. These drugs have 99% non-epigenetic trials.

TIER 2 (Oncology Filter): For core epi drugs (HDAC, BET, EZH2, etc.) -
    query by drug name + oncology conditions filter.

TIER 3 (Discovery): Query by mechanism keywords to find NEW trials
    we don't know about yet.

API: ClinicalTrials.gov API v2 (https://clinicaltrials.gov/data-api/api)
Rate Limit: ~50 requests/minute (we use 2-sec delays)

Usage:
    python -m backend.etl.32_fetch_trial_dates
    python -m backend.etl.32_fetch_trial_dates --tier tier2
    python -m backend.etl.32_fetch_trial_dates --drug VORINOSTAT
    python -m backend.etl.32_fetch_trial_dates --dry-run
"""

import argparse
import os
import sys
import time
import csv
from datetime import datetime, timezone
from typing import Optional
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.etl.supabase_client import supabase

# ============================================================================
# Configuration
# ============================================================================

CTGOV_API = "https://clinicaltrials.gov/api/v2/studies"

# Oncology conditions for Tier 2 filtering
ONCOLOGY_CONDITIONS = [
    "neoplasm", "neoplasms", "cancer", "tumor", "tumour",
    "carcinoma", "leukemia", "lymphoma", "myeloma", "sarcoma",
    "melanoma", "glioma", "glioblastoma", "malignant", "oncology",
    "acute myeloid", "multiple myeloma", "non-hodgkin", "hodgkin",
    "breast cancer", "lung cancer", "prostate cancer", "colorectal",
    "pancreatic cancer", "ovarian cancer", "bladder cancer",
    "hepatocellular", "renal cell", "head and neck cancer"
]

# Mechanism keywords for Tier 3 discovery
MECHANISM_QUERIES = [
    "HDAC inhibitor",
    "BET inhibitor",
    "EZH2 inhibitor",
    "DNMT inhibitor",
    "DOT1L inhibitor",
    "LSD1 inhibitor",
    "PRMT5 inhibitor",
    "Menin inhibitor",
    "IDH inhibitor",
    "bromodomain inhibitor",
    "histone deacetylase",
    "epigenetic therapy",
    "epigenetic modifier",
]

# Fields to fetch from CT.gov
CTGOV_FIELDS = [
    "NCTId",
    "BriefTitle",
    "OfficialTitle",
    "OverallStatus",
    "Phase",
    "StartDate",
    "StartDateType",
    "PrimaryCompletionDate",
    "PrimaryCompletionDateType",
    "CompletionDate",
    "CompletionDateType",
    "ResultsFirstPostDate",
    "EnrollmentCount",
    "EnrollmentType",
    "LeadSponsorName",
    "LeadSponsorClass",
    "CollaboratorName",
    "StudyType",
    "InterventionName",
    "ConditionName",
]

# ============================================================================
# API Functions
# ============================================================================

def fetch_study_by_nct(nct_id: str) -> Optional[dict]:
    """Fetch a single study by NCT ID (Tier 1)."""
    url = f"{CTGOV_API}/{nct_id}"
    params = {"format": "json"}

    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 404:
            print(f"    NCT ID not found: {nct_id}")
            return None
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"    Error fetching {nct_id}: {e}")
        return None


def fetch_studies_by_query(
    intervention: str = None,
    condition: str = None,
    sponsor: str = None,
    page_size: int = 100,
    max_pages: int = 5
) -> list:
    """Fetch studies matching query parameters (Tier 2/3).

    Uses CT.gov API v2 simple query parameters:
    - query.intr: Intervention/treatment name
    - query.cond: Condition/disease
    - query.spons: Sponsor name
    """
    all_studies = []
    page_token = None

    for page in range(max_pages):
        params = {
            "format": "json",
            "pageSize": page_size,
        }

        # Use simple query parameters (not AREA syntax)
        if intervention:
            params["query.intr"] = intervention
        if condition:
            # For multiple conditions, just use OR in a single string
            params["query.cond"] = condition.replace("|", " OR ")
        if sponsor:
            params["query.spons"] = sponsor

        # Filter to relevant statuses
        params["filter.overallStatus"] = "NOT_YET_RECRUITING,RECRUITING,ENROLLING_BY_INVITATION,ACTIVE_NOT_RECRUITING,COMPLETED"

        if page_token:
            params["pageToken"] = page_token

        try:
            response = requests.get(CTGOV_API, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            studies = data.get("studies", [])
            if not studies:
                break

            all_studies.extend(studies)
            print(f"    Page {page + 1}: fetched {len(studies)} studies (total: {len(all_studies)})")

            # Check for next page
            page_token = data.get("nextPageToken")
            if not page_token:
                break

            # Rate limiting
            time.sleep(2)

        except requests.RequestException as e:
            print(f"    Error on page {page + 1}: {e}")
            break

    return all_studies


def parse_study(study: dict, drug_id: str = None, drug_name: str = None, query_tier: str = None) -> dict:
    """Parse CT.gov study into our schema."""
    proto = study.get("protocolSection", {})

    id_module = proto.get("identificationModule", {})
    status_module = proto.get("statusModule", {})
    design_module = proto.get("designModule", {})
    sponsor_module = proto.get("sponsorCollaboratorsModule", {})
    enrollment_info = design_module.get("enrollmentInfo", {})

    # Parse dates
    pcd = status_module.get("primaryCompletionDateStruct", {})
    scd = status_module.get("completionDateStruct", {})
    start = status_module.get("startDateStruct", {})

    # Get sponsor info
    lead_sponsor = sponsor_module.get("leadSponsor", {})
    collaborators = sponsor_module.get("collaborators", [])

    # Parse phase (can be list)
    phases = design_module.get("phases", [])
    phase = phases[0] if phases else None

    nct_id = id_module.get("nctId")

    return {
        "nct_id": nct_id,
        "trial_title": id_module.get("briefTitle"),
        "primary_completion_date": parse_date(pcd.get("date")),
        "primary_completion_type": pcd.get("type"),
        "study_completion_date": parse_date(scd.get("date")),
        "study_completion_type": scd.get("type"),
        "start_date": parse_date(start.get("date")),
        "results_first_posted": parse_date(status_module.get("resultsFirstPostedDateStruct", {}).get("date")),
        "phase": phase,
        "status": status_module.get("overallStatus"),
        "drug_id": drug_id,
        "drug_name": drug_name,
        "lead_sponsor": lead_sponsor.get("name"),
        "lead_sponsor_type": lead_sponsor.get("class"),
        "collaborators": [c.get("name") for c in collaborators] if collaborators else None,
        "study_type": design_module.get("studyType"),
        "enrollment": enrollment_info.get("count"),
        "enrollment_type": enrollment_info.get("type"),
        "source": "clinicaltrials.gov",
        "source_url": f"https://clinicaltrials.gov/study/{nct_id}",
        "query_tier": query_tier,
        "last_api_update": datetime.now(timezone.utc).isoformat(),
    }


def parse_date(date_str: str) -> Optional[str]:
    """Parse CT.gov date string to ISO format."""
    if not date_str:
        return None

    # CT.gov uses formats like "2025-03", "2025-03-15", "March 2025"
    try:
        # Try full date first
        if len(date_str) == 10:  # YYYY-MM-DD
            return date_str
        elif len(date_str) == 7:  # YYYY-MM
            return f"{date_str}-01"  # Default to first of month
        else:
            # Try parsing other formats
            for fmt in ["%B %Y", "%b %Y", "%Y"]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
    except Exception:
        pass

    return None


# ============================================================================
# Tier Functions
# ============================================================================

def run_tier1_curated(dry_run: bool = False) -> dict:
    """Tier 1: Fetch only curated NCT IDs for PCSK9/TTR/E2F drugs."""
    print("\n" + "=" * 60)
    print("TIER 1: Curated NCT IDs")
    print("=" * 60)

    stats = {"found": 0, "inserted": 0, "updated": 0, "errors": 0}

    # Get curated trials from database
    curated = supabase.table("ci_curated_trials").select("*").execute()

    if not curated.data:
        # Fall back to CSV file
        print("  No curated trials in database, loading from CSV...")
        csv_path = os.path.join(os.path.dirname(__file__), "seed_curated_trials.csv")

        if os.path.exists(csv_path):
            with open(csv_path, "r") as f:
                reader = csv.DictReader(f)
                curated_list = [row for row in reader if not row["drug_name"].startswith("#")]
        else:
            print("  No curated trials found. Skipping Tier 1.")
            return stats
    else:
        curated_list = curated.data

    print(f"  Found {len(curated_list)} curated trials to fetch")

    # Get drug ID mapping
    drugs = supabase.table("epi_drugs").select("id, name").execute()
    drug_map = {d["name"]: d["id"] for d in drugs.data}

    for trial in curated_list:
        nct_id = trial.get("nct_id")
        drug_name = trial.get("drug_name")
        drug_id = drug_map.get(drug_name)

        print(f"  Fetching {nct_id} ({drug_name})...")

        study = fetch_study_by_nct(nct_id)
        if not study:
            stats["errors"] += 1
            continue

        stats["found"] += 1
        parsed = parse_study(study, drug_id=drug_id, drug_name=drug_name, query_tier="tier1_curated")

        if dry_run:
            print(f"    [DRY RUN] Would upsert: {parsed['nct_id']} - {parsed['trial_title'][:50]}...")
        else:
            upsert_trial(parsed, stats)

        time.sleep(1)

    return stats


def run_tier2_oncology(drug_filter: str = None, dry_run: bool = False) -> dict:
    """Tier 2: Fetch trials for core epi drugs with oncology filter."""
    print("\n" + "=" * 60)
    print("TIER 2: Drug + Oncology Filter")
    print("=" * 60)

    stats = {"found": 0, "inserted": 0, "updated": 0, "errors": 0}

    # Get Tier 2 drugs
    query = supabase.table("epi_drugs").select("id, name").eq("ctgov_query_tier", "tier2_oncology")

    if drug_filter:
        query = query.eq("name", drug_filter.upper())

    drugs = query.execute()

    print(f"  Found {len(drugs.data)} Tier 2 drugs to query")

    # Simple oncology condition filter
    oncology_filter = "cancer OR neoplasm OR leukemia OR lymphoma OR myeloma OR carcinoma"

    for drug in drugs.data:
        drug_name = drug["name"]
        drug_id = drug["id"]

        print(f"\n  Querying: {drug_name}")

        studies = fetch_studies_by_query(
            intervention=drug_name,
            condition=oncology_filter,
            page_size=50,
            max_pages=3
        )

        print(f"    Found {len(studies)} oncology trials")
        stats["found"] += len(studies)

        for study in studies:
            parsed = parse_study(study, drug_id=drug_id, drug_name=drug_name, query_tier="tier2_oncology")

            if dry_run:
                pcd = parsed.get("primary_completion_date", "N/A")
                print(f"    [DRY RUN] {parsed['nct_id']} | Phase: {parsed['phase']} | PCD: {pcd}")
            else:
                upsert_trial(parsed, stats)

        # Rate limiting between drugs
        time.sleep(3)

    return stats


def run_tier3_discovery(dry_run: bool = False) -> dict:
    """Tier 3: Discover NEW trials by mechanism keywords."""
    print("\n" + "=" * 60)
    print("TIER 3: Mechanism-Based Discovery")
    print("=" * 60)

    stats = {"found": 0, "inserted": 0, "updated": 0, "errors": 0}

    # Get existing NCT IDs to avoid duplicates
    existing = supabase.table("ci_trial_calendar").select("nct_id").execute()
    existing_ncts = {t["nct_id"] for t in existing.data}

    print(f"  {len(existing_ncts)} trials already in database")

    for mechanism in MECHANISM_QUERIES:
        print(f"\n  Searching: '{mechanism}' + cancer")

        studies = fetch_studies_by_query(
            intervention=mechanism,
            condition="cancer|neoplasm|leukemia|lymphoma|myeloma",
            page_size=50,
            max_pages=2
        )

        new_studies = [s for s in studies if s.get("protocolSection", {}).get("identificationModule", {}).get("nctId") not in existing_ncts]

        print(f"    Found {len(studies)} trials, {len(new_studies)} are new")
        stats["found"] += len(new_studies)

        for study in new_studies:
            parsed = parse_study(study, query_tier="tier3_discovery")

            if dry_run:
                print(f"    [DRY RUN] NEW: {parsed['nct_id']} - {parsed['trial_title'][:50]}...")
            else:
                upsert_trial(parsed, stats)
                existing_ncts.add(parsed["nct_id"])

        time.sleep(3)

    return stats


# ============================================================================
# Database Functions
# ============================================================================

def upsert_trial(trial: dict, stats: dict) -> None:
    """Upsert a trial to ci_trial_calendar."""
    try:
        # Check if exists
        existing = supabase.table("ci_trial_calendar").select("id").eq("nct_id", trial["nct_id"]).execute()

        if existing.data:
            # Update
            trial["updated_at"] = datetime.now(timezone.utc).isoformat()
            supabase.table("ci_trial_calendar").update(trial).eq("nct_id", trial["nct_id"]).execute()
            stats["updated"] += 1
        else:
            # Insert
            supabase.table("ci_trial_calendar").insert(trial).execute()
            stats["inserted"] += 1

    except Exception as e:
        print(f"    Error upserting {trial['nct_id']}: {e}")
        stats["errors"] += 1


def log_etl_run(stats: dict, tier: str) -> None:
    """Log ETL run to etl_refresh_log."""
    try:
        supabase.table("etl_refresh_log").insert({
            "entity_type": "trial_calendar",
            "api_source": f"clinicaltrials.gov_{tier}",
            "records_found": stats["found"],
            "records_inserted": stats["inserted"],
            "records_skipped": stats.get("updated", 0),
            "status": "success" if stats["errors"] == 0 else "partial",
            "error_message": f"{stats['errors']} errors" if stats["errors"] > 0 else None,
        }).execute()
    except Exception as e:
        print(f"  Warning: Could not log ETL run: {e}")


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Fetch clinical trial dates from CT.gov")
    parser.add_argument("--tier", choices=["tier1", "tier2", "tier3", "all"], default="all",
                        help="Which tier to run")
    parser.add_argument("--drug", type=str, help="Filter to specific drug name (Tier 2 only)")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to database")
    args = parser.parse_args()

    print("CT.gov Trial Calendar Fetcher")
    print(f"Tier: {args.tier}")
    print(f"Dry run: {args.dry_run}")

    total_stats = {"found": 0, "inserted": 0, "updated": 0, "errors": 0}

    if args.tier in ["tier1", "all"]:
        stats = run_tier1_curated(dry_run=args.dry_run)
        for k, v in stats.items():
            total_stats[k] += v
        if not args.dry_run:
            log_etl_run(stats, "tier1")

    if args.tier in ["tier2", "all"]:
        stats = run_tier2_oncology(drug_filter=args.drug, dry_run=args.dry_run)
        for k, v in stats.items():
            total_stats[k] += v
        if not args.dry_run:
            log_etl_run(stats, "tier2")

    if args.tier in ["tier3", "all"]:
        stats = run_tier3_discovery(dry_run=args.dry_run)
        for k, v in stats.items():
            total_stats[k] += v
        if not args.dry_run:
            log_etl_run(stats, "tier3")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Trials found: {total_stats['found']}")
    print(f"  Inserted: {total_stats['inserted']}")
    print(f"  Updated: {total_stats['updated']}")
    print(f"  Errors: {total_stats['errors']}")


if __name__ == "__main__":
    main()
