"""
ETL Script: 23_seed_target_annotations.py
Adds target-level annotations for IO exhaustion, resistance roles, and aging relevance.

These annotations help prioritize targets for:
- IO combination studies (io_exhaustion_axis, io_combo_priority)
- Understanding resistance mechanisms (epi_resistance_role)
- Aging/longevity research overlap (aging_clock_relevance)

Usage:
    python -m backend.etl.23_seed_target_annotations
"""

import csv
from pathlib import Path
from backend.etl.supabase_client import supabase


def load_annotations_csv():
    """Load target annotations from CSV."""
    csv_path = Path(__file__).parent / "seed_target_annotations.csv"
    annotations = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            annotations.append(row)
    return annotations


def seed_annotations():
    """Update targets with annotations."""
    if not supabase:
        print("Supabase not configured. Skipping.")
        return

    annotations = load_annotations_csv()
    print(f"Loaded {len(annotations)} target annotations from CSV")

    updated = 0
    not_found = 0

    for ann in annotations:
        symbol = ann["symbol"].strip()

        # Find target by symbol
        result = supabase.table("epi_targets").select("id").eq("symbol", symbol).execute()

        if not result.data:
            print(f"  [SKIP] Target not found: {symbol}")
            not_found += 1
            continue

        target_id = result.data[0]["id"]

        # Prepare update data
        update_data = {}

        # Parse io_exhaustion_axis (boolean)
        if ann["io_exhaustion_axis"]:
            update_data["io_exhaustion_axis"] = ann["io_exhaustion_axis"].upper() == "TRUE"

        # Parse epi_resistance_role (string)
        if ann["epi_resistance_role"]:
            update_data["epi_resistance_role"] = ann["epi_resistance_role"]

        # Parse aging_clock_relevance (string)
        if ann["aging_clock_relevance"]:
            update_data["aging_clock_relevance"] = ann["aging_clock_relevance"]

        # Parse io_combo_priority (integer)
        if ann["io_combo_priority"]:
            try:
                update_data["io_combo_priority"] = int(ann["io_combo_priority"])
            except ValueError:
                pass

        # Parse annotation_notes (string)
        if ann["annotation_notes"]:
            update_data["annotation_notes"] = ann["annotation_notes"]

        if update_data:
            supabase.table("epi_targets").update(update_data).eq("id", target_id).execute()
            io_flag = "🔥" if update_data.get("io_exhaustion_axis") else "  "
            priority = update_data.get("io_combo_priority", "-")
            role = update_data.get("epi_resistance_role", "-")
            print(f"  {io_flag} {symbol}: priority={priority}, role={role}")
            updated += 1

    print(f"\n=== Summary ===")
    print(f"Updated: {updated}")
    print(f"Not found: {not_found}")


def print_io_targets():
    """Print targets flagged for IO exhaustion."""
    print("\n🔥 IO Exhaustion Axis Targets (sorted by priority):")

    result = supabase.table("epi_targets")\
        .select("symbol, io_combo_priority, epi_resistance_role")\
        .eq("io_exhaustion_axis", True)\
        .order("io_combo_priority", desc=True)\
        .execute()

    for t in result.data:
        priority = t.get("io_combo_priority", 0) or 0
        role = t.get("epi_resistance_role", "-")
        bar = "█" * (priority // 10) + "░" * (10 - priority // 10)
        print(f"  {t['symbol']:10} [{bar}] {priority:3d} ({role})")


def main():
    print("=" * 60)
    print("ETL: Seeding Target-Level Annotations")
    print("=" * 60)
    seed_annotations()
    print_io_targets()
    print("\nDone!")


if __name__ == "__main__":
    main()
