"""
10_seed_editing_assets.py

Seeds epi_editing_assets table from seed_epi_editors.csv.
Also creates/upserts target genes in epi_editing_target_genes.

Run: python -m backend.etl.10_seed_editing_assets
"""

import csv
import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from backend.etl import supabase_client


def parse_effector_domains(domain_str: str) -> list:
    """Parse effector domains from CSV string format."""
    if not domain_str:
        return []
    try:
        # The CSV has JSON array format: ["KRAB","DNMT3A","DNMT3L"]
        return json.loads(domain_str)
    except json.JSONDecodeError:
        # Fallback: split by comma
        return [d.strip().strip('"') for d in domain_str.split(",")]


def run():
    print("=" * 60)
    print("10_seed_editing_assets.py")
    print("Seeding Epigenetic Editing Assets from CSV")
    print("=" * 60)

    csv_path = os.path.join(os.path.dirname(__file__), "seed_epi_editors.csv")

    if not os.path.exists(csv_path):
        print(f"  ERROR: CSV file not found: {csv_path}")
        return

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Found {len(rows)} editing programs in seed file.\n")

    success_count = 0
    error_count = 0

    for row in rows:
        name = row.get("name", "").strip()
        if not name:
            continue

        print(f"Processing: {name}")

        # Parse phase (convert to int, 0 for preclinical)
        phase_str = row.get("phase", "0").strip()
        try:
            phase = int(phase_str)
        except ValueError:
            phase = 0

        # Parse effector domains
        effector_domains = parse_effector_domains(row.get("effector_domains", ""))

        # Build asset data
        asset_data = {
            "name": name,
            "sponsor": row.get("sponsor", "").strip() or None,
            "modality": "epigenetic_editor",
            "delivery_type": row.get("delivery_type", "").strip() or None,
            "dbd_type": row.get("dbd_type", "").strip() or None,
            "effector_type": row.get("effector_type", "").strip() or None,
            "effector_domains": effector_domains if effector_domains else None,
            "target_gene_symbol": row.get("target_gene_symbol", "").strip() or None,
            "target_locus_description": row.get("target_locus_description", "").strip() or None,
            "primary_indication": row.get("primary_indication", "").strip() or None,
            "phase": phase,
            "status": row.get("status", "unknown").strip(),
            "mechanism_summary": row.get("mechanism_summary", "").strip() or None,
        }

        try:
            asset_id = supabase_client.upsert_editing_asset(asset_data)
            if asset_id:
                print(f"  Upserted asset: {name} (ID: {asset_id[:8]}...)")
                success_count += 1

                # Also create the target gene entry if we have a symbol
                target_symbol = asset_data.get("target_gene_symbol")
                if target_symbol:
                    _create_target_gene_if_needed(target_symbol, asset_data)
            else:
                print(f"  WARN: Could not upsert {name}")
                error_count += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            error_count += 1

    print("\n" + "=" * 60)
    print(f"DONE: {success_count} assets seeded, {error_count} errors")
    print("=" * 60)


def _create_target_gene_if_needed(symbol: str, asset_data: dict):
    """Create target gene entry if it doesn't exist."""
    existing = supabase_client.get_editing_target_gene_by_symbol(symbol)
    if existing:
        return existing["id"]

    # Determine gene category based on known patterns
    category = "other"
    if symbol in ["MYC", "KRAS", "TP53", "EGFR"]:
        category = "oncogene"
    elif symbol in ["HBV", "HCV", "HIV"]:
        category = "viral_target"
    elif symbol in ["DUX4", "DMD", "HTT"]:
        category = "disease_gene"

    # Check if this is also a classic epi target
    epi_target = supabase_client.get_epi_target_by_symbol(symbol)
    is_classic = epi_target is not None
    epi_target_id = epi_target["id"] if epi_target else None

    target_gene_data = {
        "symbol": symbol,
        "full_name": None,  # Will be enriched later
        "gene_category": category,
        "is_classic_epi_target": is_classic,
        "epi_target_id": epi_target_id,
        "editor_ready_status": "strong_candidate" if asset_data.get("phase", 0) >= 1 else "unknown",
        "primary_disease_areas": [asset_data.get("primary_indication")] if asset_data.get("primary_indication") else None,
    }

    try:
        gene_id = supabase_client.upsert_editing_target_gene(target_gene_data)
        if gene_id:
            print(f"    Created target gene: {symbol} (ID: {gene_id[:8]}...)")
    except Exception as e:
        print(f"    WARN: Could not create target gene {symbol}: {e}")


if __name__ == "__main__":
    run()
