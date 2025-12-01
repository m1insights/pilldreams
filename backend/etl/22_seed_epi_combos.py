"""
ETL Script: 22_seed_epi_combos.py
Seeds combination therapy data from curated CSV.

Combination categories:
- epi+IO: Epigenetic drug + checkpoint inhibitor
- epi+KRAS: Epigenetic drug + KRAS inhibitor
- epi+radiation: Epigenetic drug + radiotherapy
- epi+Venetoclax: Epigenetic drug + BCL2 inhibitor
- epi+chemotherapy: Epigenetic drug + chemotherapy

Usage:
    python -m backend.etl.22_seed_epi_combos
"""

import csv
from pathlib import Path
from backend.etl.supabase_client import (
    supabase,
    insert_epi_combo,
    get_drug_by_name_exact,
    get_indication_by_name,
    insert_epi_indication,
)


def load_combos_csv():
    """Load combination data from CSV."""
    csv_path = Path(__file__).parent / "seed_epi_combos.csv"
    combos = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            combos.append(row)
    return combos


def seed_combos():
    """Seed combination therapy data into epi_combos table."""
    if not supabase:
        print("Supabase not configured. Skipping.")
        return

    combos = load_combos_csv()
    print(f"Loaded {len(combos)} combination entries from CSV")

    added = 0
    skipped_no_drug = 0
    skipped_no_indication = 0

    for combo in combos:
        epi_drug_name = combo["epi_drug_name"].strip()
        indication_name = combo["indication_name"].strip()

        # Look up epigenetic drug
        drug = get_drug_by_name_exact(epi_drug_name)
        if not drug:
            print(f"  [SKIP] Drug not found: {epi_drug_name}")
            skipped_no_drug += 1
            continue

        # Look up or create indication
        indication = get_indication_by_name(indication_name)
        if not indication:
            # Try to create indication
            print(f"  [INFO] Creating indication: {indication_name}")
            ind_id = insert_epi_indication({"name": indication_name})
            indication = {"id": ind_id}
            if not ind_id:
                print(f"  [SKIP] Could not create indication: {indication_name}")
                skipped_no_indication += 1
                continue

        # Prepare combo data
        combo_data = {
            "epi_drug_id": drug["id"],
            "combo_label": combo["combo_label"],
            "partner_class": combo["partner_class"] if combo["partner_class"] else None,
            "partner_drug_name": combo["partner_drug_name"] if combo["partner_drug_name"] else None,
            "indication_id": indication["id"],
            "source": combo["source"],
            "notes": combo["notes"] if combo["notes"] else None,
        }

        # Parse max_phase
        if combo["max_phase"]:
            try:
                combo_data["max_phase"] = int(combo["max_phase"])
            except ValueError:
                pass

        # Add NCT ID if present
        if combo["nct_id"]:
            combo_data["nct_id"] = combo["nct_id"]

        # Insert combo
        try:
            combo_id = insert_epi_combo(combo_data)
            print(f"  [ADD] {epi_drug_name} + {combo['partner_class'] or combo['partner_drug_name']} → {indication_name}")
            added += 1
        except Exception as e:
            print(f"  [ERROR] {epi_drug_name}: {e}")

    print(f"\n=== Summary ===")
    print(f"Added: {added}")
    print(f"Skipped (drug not found): {skipped_no_drug}")
    print(f"Skipped (indication not found): {skipped_no_indication}")


def print_summary():
    """Print summary of combos by label."""
    print("\n📊 Combos by label:")
    try:
        combos = supabase.table("epi_combos").select("combo_label").execute().data
        label_counts = {}
        for c in combos:
            label = c["combo_label"]
            label_counts[label] = label_counts.get(label, 0) + 1

        for label, count in sorted(label_counts.items(), key=lambda x: -x[1]):
            print(f"  {label}: {count}")
    except Exception as e:
        print(f"  Error fetching summary: {e}")


def main():
    print("=" * 60)
    print("ETL: Seeding Epigenetic Combination Therapies")
    print("=" * 60)
    seed_combos()
    print_summary()
    print("\nDone!")


if __name__ == "__main__":
    main()
