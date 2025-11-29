"""
08_fetch_drug_candidates.py

Fetch drug candidates from Open Targets for all 67 epigenetic targets.
Stores in epi_drug_candidates staging table for review.

Filters:
- Drug type: Small molecule only (for now)
- Phase: >= 1 (any clinical development)

Usage:
    python -m backend.etl.08_fetch_drug_candidates [--min-phase 1] [--include-antibodies]
"""

import argparse
import time
from typing import Optional
from backend.etl.supabase_client import supabase
from backend.etl.open_targets import fetch_known_drugs_for_target

# Drug types we want (case-insensitive)
SMALL_MOLECULE_TYPES = {"small molecule", "small_molecule", "smallmolecule"}
ANTIBODY_TYPES = {"antibody", "antibody drug conjugate"}


def get_all_targets():
    """Fetch all targets from epi_targets."""
    result = supabase.table("epi_targets").select("id, symbol, ot_target_id").execute()
    return result.data


def get_existing_gold_drugs():
    """Get set of OT drug IDs already in epi_drugs (gold set)."""
    result = supabase.table("epi_drugs").select("ot_drug_id").execute()
    return {d["ot_drug_id"] for d in result.data if d.get("ot_drug_id")}


def fetch_candidates_for_target(
    target_id: int,
    target_symbol: str,
    ot_target_id: str,
    min_phase: float = 1.0,
    include_antibodies: bool = False,
    existing_gold: set = None,
):
    """
    Fetch drug candidates for a single target from Open Targets.
    Returns list of candidate dicts ready for insertion.
    """
    if not ot_target_id:
        print(f"  ⚠️  No OT target ID for {target_symbol}, skipping")
        return []

    try:
        rows = fetch_known_drugs_for_target(ot_target_id)
    except Exception as e:
        print(f"  ❌ Error fetching drugs for {target_symbol}: {e}")
        return []

    candidates = []
    existing_gold = existing_gold or set()

    for row in rows:
        drug = row.get("drug", {})
        disease = row.get("disease", {})

        ot_drug_id = drug.get("id")
        drug_type = drug.get("drugType", "").lower()
        max_phase = drug.get("maximumClinicalTrialPhase") or 0
        indication_phase = row.get("phase") or 0

        # Skip if already in gold set
        if ot_drug_id in existing_gold:
            continue

        # Filter by drug type
        is_small_molecule = drug_type in SMALL_MOLECULE_TYPES
        is_antibody = drug_type in ANTIBODY_TYPES

        if not is_small_molecule and not (include_antibodies and is_antibody):
            continue

        # Filter by phase
        if max_phase < min_phase:
            continue

        candidates.append({
            "ot_drug_id": ot_drug_id,
            "chembl_id": ot_drug_id if ot_drug_id.startswith("CHEMBL") else None,
            "name": drug.get("name"),
            "drug_type": drug.get("drugType"),
            "max_clinical_phase": max_phase,
            "source_target_id": str(target_id),  # UUID as string
            "source_target_symbol": target_symbol,
            "ot_target_id": ot_target_id,
            "mechanism_of_action": row.get("mechanismOfAction"),
            "indication_efo_id": disease.get("id"),
            "indication_name": disease.get("name"),
            "indication_phase": indication_phase,
            "status": "pending",
        })

    return candidates


def upsert_candidates(candidates: list):
    """Insert candidates, skip duplicates."""
    if not candidates:
        return 0

    inserted = 0
    for c in candidates:
        try:
            supabase.table("epi_drug_candidates").upsert(
                c,
                on_conflict="ot_drug_id,ot_target_id,indication_efo_id"
            ).execute()
            inserted += 1
        except Exception as e:
            # Likely duplicate, skip
            if "duplicate" not in str(e).lower():
                print(f"    ⚠️  Error inserting {c['name']}: {e}")

    return inserted


def main(min_phase: float = 1.0, include_antibodies: bool = False):
    """Main entry point."""
    print("=" * 60)
    print("PHASE4 ANALYTICS - Drug Candidate Discovery")
    print("=" * 60)
    print(f"Min Phase: {min_phase}")
    print(f"Include Antibodies: {include_antibodies}")
    print()

    # Get existing gold drugs to exclude
    existing_gold = get_existing_gold_drugs()
    print(f"Excluding {len(existing_gold)} existing gold drugs")
    print()

    # Get all targets
    targets = get_all_targets()
    print(f"Processing {len(targets)} epigenetic targets...")
    print()

    total_candidates = 0
    total_inserted = 0

    for i, target in enumerate(targets, 1):
        target_id = target["id"]
        symbol = target["symbol"]
        ot_target_id = target.get("ot_target_id")

        print(f"[{i:2}/{len(targets)}] {symbol}...", end=" ", flush=True)

        candidates = fetch_candidates_for_target(
            target_id=target_id,
            target_symbol=symbol,
            ot_target_id=ot_target_id,
            min_phase=min_phase,
            include_antibodies=include_antibodies,
            existing_gold=existing_gold,
        )

        if candidates:
            inserted = upsert_candidates(candidates)
            total_candidates += len(candidates)
            total_inserted += inserted
            print(f"found {len(candidates)} candidates, inserted {inserted}")
        else:
            print("no candidates")

        # Rate limiting
        time.sleep(0.2)

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total candidates found: {total_candidates}")
    print(f"Total inserted: {total_inserted}")
    print()

    # Show quick summary
    summary = supabase.table("epi_drug_candidates").select(
        "ot_drug_id, name, max_clinical_phase, drug_type",
        count="exact"
    ).eq("status", "pending").execute()

    print(f"Unique drugs in staging: {summary.count}")

    # Count by phase
    by_phase = {}
    for row in summary.data:
        phase = row.get("max_clinical_phase", 0)
        by_phase[phase] = by_phase.get(phase, 0) + 1

    print("\nBy Max Phase:")
    for phase in sorted(by_phase.keys(), reverse=True):
        print(f"  Phase {phase}: {by_phase[phase]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch drug candidates from Open Targets")
    parser.add_argument("--min-phase", type=float, default=1.0, help="Minimum clinical phase (default: 1)")
    parser.add_argument("--include-antibodies", action="store_true", help="Include antibodies (default: small molecules only)")

    args = parser.parse_args()
    main(min_phase=args.min_phase, include_antibodies=args.include_antibodies)
