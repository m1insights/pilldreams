"""
04c_compute_drug_phases.py - Fetch clinical trial phase data from ChEMBL

This script:
1. Gets all drugs with ChEMBL IDs
2. Queries ChEMBL API for max_phase
3. Updates epi_drugs.max_phase

Phase values from ChEMBL:
- 0 = Preclinical
- 1 = Phase 1
- 2 = Phase 2
- 3 = Phase 3
- 4 = Approved

IMPORTANT: Before running, ensure the max_phase column exists:
  ALTER TABLE epi_drugs ADD COLUMN IF NOT EXISTS max_phase INTEGER;
"""

import requests
import time
from backend.etl.supabase_client import supabase

CHEMBL_BASE = "https://www.ebi.ac.uk/chembl/api/data"


def fetch_chembl_phase(chembl_id: str) -> int | None:
    """Fetch max_phase from ChEMBL API for a given molecule."""
    try:
        url = f"{CHEMBL_BASE}/molecule/{chembl_id}.json"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            max_phase = data.get("max_phase")
            if max_phase is not None:
                # ChEMBL returns floats like 3.0, convert to int
                return int(float(max_phase))
        return None
    except Exception as e:
        print(f"  Error fetching {chembl_id}: {e}")
        return None


def main():
    print("=== Fetching Drug Phases from ChEMBL ===\n")

    # Get all drugs with ChEMBL IDs
    result = supabase.table("epi_drugs").select("id, name, chembl_id, fda_approved").execute()
    drugs = result.data

    print(f"Found {len(drugs)} drugs\n")

    updated = 0
    skipped = 0
    errors = 0

    for drug in drugs:
        chembl_id = drug.get("chembl_id")
        name = drug["name"]

        if not chembl_id:
            print(f"  {name}: No ChEMBL ID, skipping")
            skipped += 1
            continue

        # Fetch phase from ChEMBL
        phase = fetch_chembl_phase(chembl_id)

        if phase is not None:
            # If FDA approved in our data but ChEMBL shows lower phase, use 4
            if drug.get("fda_approved") and phase < 4:
                print(f"  {name}: ChEMBL shows Phase {phase} but marked FDA approved, using Phase 4")
                phase = 4

            try:
                supabase.table("epi_drugs").update({"max_phase": phase}).eq("id", drug["id"]).execute()
                print(f"  {name}: Phase {phase}")
                updated += 1
            except Exception as e:
                print(f"  {name}: Error updating - {e}")
                errors += 1
        else:
            # Check if FDA approved - if so, set to phase 4
            if drug.get("fda_approved"):
                try:
                    supabase.table("epi_drugs").update({"max_phase": 4}).eq("id", drug["id"]).execute()
                    print(f"  {name}: FDA approved, setting Phase 4")
                    updated += 1
                except Exception as e:
                    print(f"  {name}: Error updating - {e}")
                    errors += 1
            else:
                print(f"  {name}: No phase data in ChEMBL")
                skipped += 1

        # Rate limit to avoid hitting ChEMBL too hard
        time.sleep(0.2)

    print(f"\n=== Summary ===")
    print(f"Updated: {updated}")
    print(f"Skipped: {skipped}")
    print(f"Errors: {errors}")


if __name__ == "__main__":
    main()
