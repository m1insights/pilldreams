"""
11_map_editing_targets.py

Maps editing assets to their target genes and enriches gene information
from Open Targets and UniProt.

Run: python -m backend.etl.11_map_editing_targets
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from backend.etl import supabase_client, open_targets


def run():
    print("=" * 60)
    print("11_map_editing_targets.py")
    print("Mapping Editing Assets to Target Genes")
    print("=" * 60)

    # Get all editing assets
    assets = supabase_client.get_all_editing_assets()
    print(f"Found {len(assets)} editing assets.\n")

    for asset in assets:
        name = asset["name"]
        target_symbol = asset.get("target_gene_symbol")

        if not target_symbol:
            print(f"Skipping {name}: No target gene symbol")
            continue

        print(f"Processing: {name} -> {target_symbol}")

        # Get or create the target gene
        target_gene = supabase_client.get_editing_target_gene_by_symbol(target_symbol)

        if not target_gene:
            # Create new target gene entry
            target_gene_data = _enrich_target_gene(target_symbol)
            if target_gene_data:
                gene_id = supabase_client.upsert_editing_target_gene(target_gene_data)
                if gene_id:
                    print(f"  Created target gene: {target_symbol}")
                    target_gene = {"id": gene_id, "symbol": target_symbol}
            else:
                print(f"  WARN: Could not create target gene for {target_symbol}")
                continue

        # Create the link between asset and target gene
        try:
            supabase_client.insert_editing_asset_target({
                "editing_asset_id": asset["id"],
                "target_gene_id": target_gene["id"],
                "is_primary_target": True,
                "mechanism_at_target": asset.get("mechanism_summary"),
            })
            print(f"  Linked {name} -> {target_symbol}")
        except Exception as e:
            print(f"  WARN: Could not link {name} -> {target_symbol}: {e}")

        # Enrich target gene with Open Targets data if missing
        if not target_gene.get("ensembl_id"):
            _enrich_and_update_target_gene(target_symbol)

    print("\n" + "=" * 60)
    print("DONE: Asset-target mapping complete")
    print("=" * 60)


def _enrich_target_gene(symbol: str) -> dict:
    """Enrich target gene data from Open Targets."""
    # Skip non-gene symbols (viruses, etc.)
    if symbol in ["HBV", "HCV", "HIV", "Various"]:
        return {
            "symbol": symbol,
            "gene_category": "viral_target" if symbol != "Various" else "other",
            "editor_ready_status": "unknown",
        }

    # Try to find in Open Targets
    try:
        ot_target = open_targets.search_target_by_symbol(symbol)
        if ot_target:
            ot_id = ot_target["id"]
            details = open_targets.fetch_target_details(ot_id)

            uniprot_id = None
            if details and details.get("proteinAnnotations"):
                uniprot_id = details["proteinAnnotations"].get("id")

            # Check if this symbol exists in epi_targets
            epi_target = supabase_client.get_epi_target_by_symbol(symbol)

            return {
                "symbol": symbol,
                "full_name": ot_target.get("approvedName"),
                "ensembl_id": ot_id,
                "uniprot_id": uniprot_id,
                "gene_category": _classify_gene(symbol),
                "is_classic_epi_target": epi_target is not None,
                "epi_target_id": epi_target["id"] if epi_target else None,
                "editor_ready_status": "unknown",
            }
    except Exception as e:
        print(f"    WARN: Could not enrich {symbol} from Open Targets: {e}")

    return {
        "symbol": symbol,
        "gene_category": _classify_gene(symbol),
        "editor_ready_status": "unknown",
    }


def _enrich_and_update_target_gene(symbol: str):
    """Fetch Open Targets data and update existing target gene entry."""
    if symbol in ["HBV", "HCV", "HIV", "Various"]:
        return

    try:
        ot_target = open_targets.search_target_by_symbol(symbol)
        if ot_target:
            ot_id = ot_target["id"]
            details = open_targets.fetch_target_details(ot_id)

            uniprot_id = None
            if details and details.get("proteinAnnotations"):
                uniprot_id = details["proteinAnnotations"].get("id")

            update_data = {
                "symbol": symbol,
                "full_name": ot_target.get("approvedName"),
                "ensembl_id": ot_id,
                "uniprot_id": uniprot_id,
            }

            supabase_client.upsert_editing_target_gene(update_data)
            print(f"    Enriched {symbol} with Open Targets data")
    except Exception as e:
        print(f"    WARN: Could not enrich {symbol}: {e}")


def _classify_gene(symbol: str) -> str:
    """Classify gene category based on known patterns."""
    oncogenes = ["MYC", "MYCN", "KRAS", "NRAS", "HRAS", "EGFR", "BRAF", "BCL2", "BCL6", "ABL1"]
    disease_genes = ["DUX4", "DMD", "HTT", "CFTR", "SMN1", "FXN", "MECP2", "PCSK9"]
    viral_targets = ["HBV", "HCV", "HIV", "HPV", "EBV"]

    if symbol in oncogenes:
        return "oncogene"
    elif symbol in disease_genes:
        return "disease_gene"
    elif symbol in viral_targets:
        return "viral_target"
    else:
        return "other"


if __name__ == "__main__":
    run()
