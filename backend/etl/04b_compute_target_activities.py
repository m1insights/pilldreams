"""
ETL Script: 04b_compute_target_activities.py
Computes per-target activity breakdown from ChEMBL for potency visualization.

This provides detailed potency data per target, enabling:
- Visual comparison of drug selectivity across targets
- Understanding of on-target vs off-target activity
- Richer chemistry insights than aggregate metrics alone

Usage:
    python -m backend.etl.04b_compute_target_activities
"""

import math
import statistics
import requests
from backend.etl.supabase_client import supabase

CHEMBL_API_URL = "https://www.ebi.ac.uk/chembl/api/data"


def fetch_target_activities(chembl_molecule_id: str) -> list:
    """
    Fetch per-target activity breakdown from ChEMBL.
    Returns list of dicts with target-level metrics.
    """
    url = f"{CHEMBL_API_URL}/activity"
    params = {
        "molecule_chembl_id": chembl_molecule_id,
        "standard_type__in": "Ki,Kd,IC50,EC50",
        "standard_units": "nM",
        "limit": 500,
        "format": "json"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        activities = data.get("activities", [])
    except Exception as e:
        print(f"  ❌ Error fetching ChEMBL: {e}")
        return []

    # Group by target
    targets = {}

    for act in activities:
        # Quality filter: Binding or Functional assays only
        if act.get("assay_type") not in ["B", "F"]:
            continue

        target_chembl = act.get("target_chembl_id", "")
        target_name = act.get("target_pref_name", "Unknown")
        target_type = act.get("target_type", "")
        std_type = act.get("standard_type", "")
        val = act.get("standard_value")

        if not val or not target_chembl:
            continue

        try:
            val_nm = float(val)
            if val_nm <= 0:
                continue
            p_val = 9 - math.log10(val_nm)
        except:
            continue

        if target_chembl not in targets:
            targets[target_chembl] = {
                "target_chembl_id": target_chembl,
                "target_name": target_name,
                "target_type": target_type,
                "pvals": [],
                "values_nm": [],
                "activity_types": set()
            }

        targets[target_chembl]["pvals"].append(p_val)
        targets[target_chembl]["values_nm"].append(val_nm)
        targets[target_chembl]["activity_types"].add(std_type)

    # Convert to list with computed metrics
    results = []
    for target_id, data in targets.items():
        pvals = data["pvals"]
        values = data["values_nm"]

        results.append({
            "target_chembl_id": target_id,
            "target_name": data["target_name"],
            "target_type": data["target_type"],
            "best_pact": max(pvals) if pvals else None,
            "median_pact": statistics.median(pvals) if pvals else None,
            "best_value_nm": min(values) if values else None,  # Lower nM = more potent
            "n_activities": len(pvals),
            "activity_types": list(data["activity_types"])
        })

    # Sort by best potency (highest first)
    results.sort(key=lambda x: x["best_pact"] or 0, reverse=True)
    return results


def upsert_target_activity(drug_id: str, data: dict):
    """Insert or update target activity record."""
    existing = supabase.table("chembl_target_activities").select("id")\
        .eq("drug_id", drug_id)\
        .eq("target_chembl_id", data["target_chembl_id"]).execute()

    record = {
        "drug_id": drug_id,
        "target_chembl_id": data["target_chembl_id"],
        "target_name": data["target_name"],
        "target_type": data["target_type"],
        "best_pact": data["best_pact"],
        "median_pact": data["median_pact"],
        "best_value_nm": data["best_value_nm"],
        "n_activities": data["n_activities"],
        "activity_types": data["activity_types"],
    }

    if existing.data:
        supabase.table("chembl_target_activities").update(record)\
            .eq("id", existing.data[0]["id"]).execute()
    else:
        supabase.table("chembl_target_activities").insert(record).execute()


def run():
    print("=" * 60)
    print("ETL: Computing Per-Target Activity Breakdown")
    print("=" * 60)

    if not supabase:
        print("❌ Supabase not configured")
        return

    # Fetch all drugs with ChEMBL IDs
    drugs = supabase.table("epi_drugs").select("id, name, chembl_id").execute().data
    print(f"Found {len(drugs)} drugs\n")

    processed = 0
    skipped = 0

    for drug in drugs:
        drug_id = drug["id"]
        name = drug["name"]
        chembl_id = drug.get("chembl_id")

        if not chembl_id or not chembl_id.startswith("CHEMBL"):
            skipped += 1
            continue

        print(f"Processing {name} ({chembl_id})...")

        # Fetch target activities
        activities = fetch_target_activities(chembl_id)

        if not activities:
            print(f"  ⚠️ No target activities found")
            continue

        # Store each target's data
        for act in activities:
            upsert_target_activity(drug_id, act)

        # Print summary
        top = activities[0] if activities else {}
        print(f"  ✅ {len(activities)} targets | Best: {top.get('target_name', 'N/A')[:30]}... "
              f"pXC50={top.get('best_pact', 0):.2f}")
        processed += 1

    print(f"\n{'=' * 60}")
    print(f"Processed: {processed} drugs")
    print(f"Skipped (no ChEMBL ID): {skipped} drugs")
    print("=" * 60)


if __name__ == "__main__":
    run()
