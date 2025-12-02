"""
ETL 34: Detect Changes Across All Entities

Compares current database state with previous snapshots.
Logs all changes to ci_change_log with significance classification.

Automation: Runs daily after all other ETLs complete

Usage:
    python -m backend.etl.34_detect_changes
    python -m backend.etl.34_detect_changes --dry-run
    python -m backend.etl.34_detect_changes --entity-type trial
"""

import os
import sys
import json
import argparse
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Any, Tuple
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY required")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ============================================================
# Significance Classification Rules
# ============================================================

SIGNIFICANCE_RULES = {
    # Drug phase changes (most important)
    ("drug", "max_phase", "2", "3"): "critical",
    ("drug", "max_phase", "3", "4"): "critical",  # Approval!
    ("drug", "max_phase", "1", "2"): "high",
    ("drug", "max_phase", "0", "1"): "high",

    # FDA approvals
    ("drug", "fda_approved", "false", "true"): "critical",

    # Trial status changes
    ("trial", "status", "*", "COMPLETED"): "high",
    ("trial", "status", "*", "TERMINATED"): "high",
    ("trial", "status", "*", "WITHDRAWN"): "high",
    ("trial", "status", "*", "SUSPENDED"): "high",
    ("trial", "status", "RECRUITING", "ACTIVE_NOT_RECRUITING"): "medium",

    # Trial date changes
    ("trial", "primary_completion_date", "*", "*"): "medium",

    # Score changes (>10 points is notable)
    ("drug", "total_score", "*", "*"): "low",  # Will be upgraded if delta > 10

    # New entities
    ("drug", "new", None, "*"): "high",
    ("trial", "new", None, "*"): "medium",
    ("patent", "new", None, "*"): "medium",
}


def classify_significance(
    entity_type: str,
    field: str,
    old_value: Optional[str],
    new_value: Optional[str]
) -> str:
    """Determine significance of a change based on rules."""

    # Check specific rules first
    for (e_type, f_name, old_pattern, new_pattern), sig in SIGNIFICANCE_RULES.items():
        if e_type != entity_type or f_name != field:
            continue

        # Check old value pattern
        old_match = (old_pattern == "*" or
                     old_pattern is None and old_value is None or
                     str(old_pattern).lower() == str(old_value or "").lower())

        # Check new value pattern
        new_match = (new_pattern == "*" or
                     str(new_pattern).lower() == str(new_value or "").lower())

        if old_match and new_match:
            return sig

    # Special case: score changes with large delta
    if field in ("total_score", "bio_score", "chem_score"):
        try:
            old_num = float(old_value) if old_value else 0
            new_num = float(new_value) if new_value else 0
            delta = abs(new_num - old_num)
            if delta >= 15:
                return "high"
            elif delta >= 10:
                return "medium"
        except (ValueError, TypeError):
            pass

    return "low"


# ============================================================
# Snapshot Management
# ============================================================

def save_snapshot(entity_type: str, entity_id: str, data: Dict[str, Any]) -> None:
    """Save a snapshot of an entity's current state."""
    today = date.today().isoformat()

    try:
        supabase.table("ci_entity_snapshots").upsert({
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "snapshot_data": data,
            "snapshot_date": today
        }, on_conflict="entity_type,entity_id,snapshot_date").execute()
    except Exception as e:
        # Table might not exist yet - skip saving
        if "PGRST205" in str(e) or "could not find" in str(e).lower():
            pass
        else:
            raise


def get_previous_snapshot(entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
    """Get the most recent snapshot before today."""
    today = date.today().isoformat()

    try:
        result = supabase.table("ci_entity_snapshots")\
            .select("snapshot_data")\
            .eq("entity_type", entity_type)\
            .eq("entity_id", str(entity_id))\
            .lt("snapshot_date", today)\
            .order("snapshot_date", desc=True)\
            .limit(1)\
            .execute()

        if result.data:
            return result.data[0]["snapshot_data"]
    except Exception as e:
        # Table might not exist yet
        if "PGRST205" in str(e) or "could not find" in str(e).lower():
            return None
        raise
    return None


# ============================================================
# Change Detection by Entity Type
# ============================================================

def detect_drug_changes(dry_run: bool = False) -> List[Dict]:
    """Detect changes in epi_drugs table."""
    print("\n📊 Detecting drug changes...")

    # Get current drugs
    result = supabase.table("epi_drugs")\
        .select("id, name, chembl_id, max_phase, fda_approved, drug_type, modality")\
        .execute()

    drugs = result.data or []
    changes = []

    for drug in drugs:
        drug_id = str(drug["id"])
        current_data = {
            "name": drug["name"],
            "max_phase": drug.get("max_phase"),
            "fda_approved": drug.get("fda_approved"),
            "drug_type": drug.get("drug_type"),
            "modality": drug.get("modality")
        }

        # Get previous snapshot
        previous = get_previous_snapshot("drug", drug_id)

        if previous is None:
            # New drug
            change = {
                "entity_type": "drug",
                "entity_id": drug_id,
                "entity_name": drug["name"],
                "change_type": "new_entity",
                "field_changed": None,
                "old_value": None,
                "new_value": drug["name"],
                "significance": classify_significance("drug", "new", None, drug["name"]),
                "source": "etl",
                "related_drug_id": drug["id"]
            }
            changes.append(change)
        else:
            # Compare fields
            for field in ["max_phase", "fda_approved"]:
                old_val = previous.get(field)
                new_val = current_data.get(field)

                if str(old_val) != str(new_val) and (old_val is not None or new_val is not None):
                    change_type = "phase_change" if field == "max_phase" else "approval"
                    change = {
                        "entity_type": "drug",
                        "entity_id": drug_id,
                        "entity_name": drug["name"],
                        "change_type": change_type,
                        "field_changed": field,
                        "old_value": str(old_val) if old_val is not None else None,
                        "new_value": str(new_val) if new_val is not None else None,
                        "significance": classify_significance("drug", field, str(old_val), str(new_val)),
                        "source": "etl",
                        "related_drug_id": drug["id"]
                    }
                    changes.append(change)

        # Save current snapshot
        if not dry_run:
            save_snapshot("drug", drug_id, current_data)

    print(f"   Found {len(changes)} drug changes")
    return changes


def detect_trial_changes(dry_run: bool = False) -> List[Dict]:
    """Detect changes in ci_trial_calendar table."""
    print("\n🔬 Detecting trial changes...")

    # Get current trials
    result = supabase.table("ci_trial_calendar")\
        .select("id, nct_id, trial_title, drug_id, drug_name, phase, status, primary_completion_date, primary_completion_type, enrollment")\
        .execute()

    trials = result.data or []
    changes = []

    for trial in trials:
        trial_id = trial["nct_id"]  # Use NCT ID as the entity identifier
        current_data = {
            "nct_id": trial["nct_id"],
            "trial_title": trial.get("trial_title"),
            "phase": trial.get("phase"),
            "status": trial.get("status"),
            "primary_completion_date": trial.get("primary_completion_date"),
            "primary_completion_type": trial.get("primary_completion_type"),
            "enrollment": trial.get("enrollment")
        }

        # Get previous snapshot
        previous = get_previous_snapshot("trial", trial_id)

        if previous is None:
            # New trial
            change = {
                "entity_type": "trial",
                "entity_id": trial_id,
                "entity_name": trial["nct_id"],
                "change_type": "new_entity",
                "field_changed": None,
                "old_value": None,
                "new_value": trial.get("trial_title", trial["nct_id"]),
                "significance": classify_significance("trial", "new", None, "*"),
                "source": "ctgov",
                "source_url": f"https://clinicaltrials.gov/study/{trial['nct_id']}",
                "related_drug_id": trial.get("drug_id")
            }
            changes.append(change)
        else:
            # Compare key fields
            fields_to_check = [
                ("status", "status_change"),
                ("phase", "phase_change"),
                ("primary_completion_date", "date_change"),
            ]

            for field, change_type in fields_to_check:
                old_val = previous.get(field)
                new_val = current_data.get(field)

                # Normalize for comparison
                old_str = str(old_val) if old_val else None
                new_str = str(new_val) if new_val else None

                if old_str != new_str and (old_val is not None or new_val is not None):
                    change = {
                        "entity_type": "trial",
                        "entity_id": trial_id,
                        "entity_name": trial["nct_id"],
                        "change_type": change_type,
                        "field_changed": field,
                        "old_value": old_str,
                        "new_value": new_str,
                        "significance": classify_significance("trial", field, old_str, new_str),
                        "source": "ctgov",
                        "source_url": f"https://clinicaltrials.gov/study/{trial['nct_id']}",
                        "related_drug_id": trial.get("drug_id")
                    }
                    changes.append(change)

        # Save current snapshot
        if not dry_run:
            save_snapshot("trial", trial_id, current_data)

    print(f"   Found {len(changes)} trial changes")
    return changes


def detect_score_changes(dry_run: bool = False) -> List[Dict]:
    """Detect changes in epi_scores table."""
    print("\n📈 Detecting score changes...")

    # Get current scores with drug names
    result = supabase.table("epi_scores")\
        .select("id, drug_id, indication_id, bio_score, chem_score, tractability_score, total_score")\
        .execute()

    scores = result.data or []

    # Get drug names for display
    drug_result = supabase.table("epi_drugs").select("id, name").execute()
    drug_names = {str(d["id"]): d["name"] for d in (drug_result.data or [])}

    changes = []

    for score in scores:
        score_id = str(score["id"])
        drug_id = str(score["drug_id"])
        drug_name = drug_names.get(drug_id, f"Drug {drug_id[:8]}")

        current_data = {
            "bio_score": score.get("bio_score"),
            "chem_score": score.get("chem_score"),
            "tractability_score": score.get("tractability_score"),
            "total_score": score.get("total_score")
        }

        # Get previous snapshot
        previous = get_previous_snapshot("score", score_id)

        if previous is not None:
            # Compare score fields
            for field in ["total_score", "bio_score", "chem_score", "tractability_score"]:
                old_val = previous.get(field)
                new_val = current_data.get(field)

                if old_val is None and new_val is None:
                    continue

                try:
                    old_num = float(old_val) if old_val is not None else None
                    new_num = float(new_val) if new_val is not None else None

                    if old_num != new_num:
                        delta = (new_num or 0) - (old_num or 0)
                        if abs(delta) >= 5:  # Only report significant score changes
                            change = {
                                "entity_type": "drug",
                                "entity_id": drug_id,
                                "entity_name": drug_name,
                                "change_type": "score_change",
                                "field_changed": field,
                                "old_value": str(round(old_num, 1)) if old_num is not None else None,
                                "new_value": str(round(new_num, 1)) if new_num is not None else None,
                                "significance": classify_significance("drug", field, str(old_num), str(new_num)),
                                "source": "etl",
                                "related_drug_id": score["drug_id"]
                            }
                            changes.append(change)
                except (ValueError, TypeError):
                    pass

        # Save current snapshot
        if not dry_run:
            save_snapshot("score", score_id, current_data)

    print(f"   Found {len(changes)} score changes")
    return changes


# ============================================================
# Log Changes to Database
# ============================================================

def log_changes(changes: List[Dict], dry_run: bool = False) -> int:
    """Insert changes into ci_change_log table."""
    if not changes:
        return 0

    if dry_run:
        print(f"\n🔍 DRY RUN - Would log {len(changes)} changes:")
        for c in changes[:10]:
            sig_emoji = {"critical": "🚨", "high": "⚠️", "medium": "📢", "low": "📝"}.get(c["significance"], "📝")
            print(f"   {sig_emoji} [{c['significance'].upper()}] {c['entity_type']}/{c['entity_name']}: {c['change_type']}")
            if c.get("old_value") and c.get("new_value"):
                print(f"      {c.get('field_changed', 'value')}: {c['old_value']} → {c['new_value']}")
        if len(changes) > 10:
            print(f"   ... and {len(changes) - 10} more")
        return 0

    # Prepare records for insert
    records = []
    for c in changes:
        # Generate change summary
        if c["change_type"] == "new_entity":
            summary = f"New {c['entity_type']}: {c['entity_name']}"
        elif c.get("old_value") and c.get("new_value"):
            summary = f"{c['entity_name']}: {c.get('field_changed', 'value')} changed from {c['old_value']} to {c['new_value']}"
        else:
            summary = f"{c['entity_name']}: {c['change_type']}"

        records.append({
            "entity_type": c["entity_type"],
            "entity_id": c["entity_id"],
            "entity_name": c["entity_name"],
            "change_type": c["change_type"],
            "field_changed": c.get("field_changed"),
            "old_value": c.get("old_value"),
            "new_value": c.get("new_value"),
            "change_summary": summary,
            "significance": c["significance"],
            "source": c.get("source", "etl"),
            "source_url": c.get("source_url"),
            "related_drug_id": c.get("related_drug_id"),
            "related_target_id": c.get("related_target_id"),
            "related_company_id": c.get("related_company_id"),
        })

    # Insert in batches
    batch_size = 100
    total_inserted = 0

    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        result = supabase.table("ci_change_log").insert(batch).execute()
        total_inserted += len(result.data) if result.data else 0

    return total_inserted


# ============================================================
# Main Entry Point
# ============================================================

def check_tables_exist() -> bool:
    """Check if required tables exist."""
    try:
        supabase.table("ci_change_log").select("id").limit(1).execute()
        supabase.table("ci_entity_snapshots").select("id").limit(1).execute()
        return True
    except Exception as e:
        if "PGRST205" in str(e):
            return False
        raise


def run_change_detection(
    entity_types: Optional[List[str]] = None,
    dry_run: bool = False
) -> Dict[str, int]:
    """Run change detection for specified entity types."""

    print("=" * 60)
    print("CI Platform: Change Detection ETL")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("=" * 60)

    # Check if tables exist
    if not check_tables_exist():
        print("\n⚠️  Required tables not found!")
        print("   Run migration: core/migration_ci_change_detection.sql")
        print("   Copy to clipboard: cat core/migration_ci_change_detection.sql | pbcopy")
        print("   Then paste in Supabase Dashboard > SQL Editor")
        if dry_run:
            print("\n   Running in DRY RUN mode - will detect changes but cannot save...")
        else:
            return {"critical": 0, "high": 0, "medium": 0, "low": 0}

    all_changes = []

    # Default to all entity types
    if entity_types is None:
        entity_types = ["drug", "trial", "score"]

    # Detect changes for each entity type
    if "drug" in entity_types:
        all_changes.extend(detect_drug_changes(dry_run))

    if "trial" in entity_types:
        all_changes.extend(detect_trial_changes(dry_run))

    if "score" in entity_types:
        all_changes.extend(detect_score_changes(dry_run))

    # Summary by significance
    sig_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for c in all_changes:
        sig_counts[c["significance"]] = sig_counts.get(c["significance"], 0) + 1

    print("\n" + "=" * 60)
    print("CHANGE SUMMARY")
    print("=" * 60)
    print(f"🚨 Critical: {sig_counts['critical']}")
    print(f"⚠️  High:     {sig_counts['high']}")
    print(f"📢 Medium:   {sig_counts['medium']}")
    print(f"📝 Low:      {sig_counts['low']}")
    print(f"   TOTAL:    {len(all_changes)}")

    # Log changes
    logged = log_changes(all_changes, dry_run)

    if not dry_run:
        print(f"\n✅ Logged {logged} changes to ci_change_log")

    return sig_counts


def main():
    parser = argparse.ArgumentParser(description="Detect changes across all entities")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without saving")
    parser.add_argument("--entity-type", type=str, help="Filter to specific entity type (drug, trial, score)")
    args = parser.parse_args()

    entity_types = [args.entity_type] if args.entity_type else None
    run_change_detection(entity_types=entity_types, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
