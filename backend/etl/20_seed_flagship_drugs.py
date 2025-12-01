"""
ETL Script: 20_seed_flagship_drugs.py
Adds high-profile missing epigenetic drugs from curated CSV.

These are flagship drugs that should be in the database:
- PRMT5 inhibitors: GSK3326595, JNJ-64619178, PRT543
- EZH2 inhibitors: CPI-1205, GSK126, SHR2554, VALEMETOSTAT
- DOT1L inhibitors: PINOMETOSTAT
- LSD1/KDM1A inhibitors: BOMEDEMSTAT, SECLIDEMSTAT, GSK2879552, CC-90011
- Menin inhibitors: ZIFTOMENIB, KO-539, SNDX-5613
- BET inhibitors: JQ1, OTX015, MIVEBRESIB, MOLIBRESIB

Usage:
    python -m backend.etl.20_seed_flagship_drugs
"""

import csv
import os
from pathlib import Path
from backend.etl.supabase_client import (
    supabase,
    upsert_epi_drug,
    insert_epi_drug_target,
    get_epi_target_by_symbol,
)


def load_flagship_drugs():
    """Load flagship drugs from CSV."""
    csv_path = Path(__file__).parent / "seed_flagship_drugs.csv"
    drugs = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            drugs.append(row)
    return drugs


def seed_flagship_drugs():
    """Seed flagship drugs into the database."""
    if not supabase:
        print("Supabase not configured. Skipping.")
        return

    drugs = load_flagship_drugs()
    print(f"Loaded {len(drugs)} flagship drugs from CSV")

    added = 0
    skipped = 0
    linked = 0

    for drug in drugs:
        drug_name = drug["name"].strip()
        target_symbol = drug["target_symbol"].strip()

        # Check if drug already exists
        existing = supabase.table("epi_drugs").select("id").eq("name", drug_name).execute()
        if existing.data:
            print(f"  [SKIP] {drug_name} already exists")
            skipped += 1
            drug_id = existing.data[0]["id"]
        else:
            # Insert drug
            drug_data = {
                "name": drug_name,
                "drug_type": drug["drug_type"],
                "chembl_id": drug["chembl_id"] if drug["chembl_id"] else None,
                "fda_approved": drug["fda_approved"].upper() == "TRUE",
                "source": drug["source"],
                "modality": "small_molecule",
            }

            # Parse max_phase
            try:
                max_phase = int(drug["max_phase"]) if drug["max_phase"] else None
                # Store max_phase in a field if available, or we'll handle it via indications
            except ValueError:
                max_phase = None

            drug_id = upsert_epi_drug(drug_data)
            print(f"  [ADD] {drug_name} (ID: {drug_id})")
            added += 1

        # Link to target
        target = get_epi_target_by_symbol(target_symbol)
        if target:
            insert_epi_drug_target({
                "drug_id": drug_id,
                "target_id": target["id"],
                "mechanism_of_action": drug["mechanism_of_action"],
                "is_primary_target": True,
            })
            print(f"    -> Linked to {target_symbol}")
            linked += 1
        else:
            print(f"    [WARN] Target {target_symbol} not found in database")

    print(f"\n=== Summary ===")
    print(f"Added: {added}")
    print(f"Skipped (existing): {skipped}")
    print(f"Target links created: {linked}")


def main():
    print("=" * 60)
    print("ETL: Seeding Flagship Epigenetic Drugs")
    print("=" * 60)
    seed_flagship_drugs()
    print("\nDone!")


if __name__ == "__main__":
    main()
