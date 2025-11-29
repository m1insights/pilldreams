"""
09_promote_candidates.py

Promote verified unique drug candidates from staging to master tables.
Then compute scores for the new drugs.

Usage:
    python -m backend.etl.09_promote_candidates
"""

from backend.etl.supabase_client import supabase
from backend.etl.open_targets import fetch_tractability

# The 7 verified unique drugs to promote
DRUGS_TO_PROMOTE = [
    "ENTINOSTAT",
    "ABEXINOSTAT",
    "TACEDINALINE",
    "MOCETINOSTAT",
    "FIMEPINOSTAT",
    "QUISINOSTAT",
    "CUDC-101",
]


def get_or_create_indication(efo_id: str, name: str) -> int:
    """Get existing indication or create new one."""
    if efo_id:
        existing = supabase.table("epi_indications").select("id").eq("efo_id", efo_id).execute()
        if existing.data:
            return existing.data[0]["id"]

    # Check by name
    if name:
        existing = supabase.table("epi_indications").select("id").eq("name", name).execute()
        if existing.data:
            return existing.data[0]["id"]

    # Create new
    result = supabase.table("epi_indications").insert({
        "name": name,
        "efo_id": efo_id,
    }).execute()
    return result.data[0]["id"]


def get_target_by_symbol(symbol: str):
    """Get target by symbol."""
    result = supabase.table("epi_targets").select("id, ot_target_id").eq("symbol", symbol).execute()
    return result.data[0] if result.data else None


def compute_tractability_score(ot_target_id: str) -> float:
    """Compute tractability score for a target."""
    if not ot_target_id:
        return 50.0  # Default middle score

    try:
        tractability = fetch_tractability(ot_target_id)
        if not tractability:
            return 50.0

        # Look for small molecule tractability
        for t in tractability:
            if t.get("modality") == "SM" and t.get("value"):
                label = t.get("label", "")
                if "Approved Drug" in label:
                    return 100.0
                elif "Structure with Ligand" in label:
                    return 85.0
                elif "High-Quality Ligand" in label:
                    return 70.0
                elif "Druggable Family" in label:
                    return 55.0
        return 40.0  # Has some tractability data but weak
    except Exception as e:
        print(f"    Error fetching tractability: {e}")
        return 50.0


def main():
    print("=" * 60)
    print("PROMOTE CANDIDATES TO MASTER LIST")
    print("=" * 60)
    print()

    # Get all candidate records for our 7 drugs
    candidates = supabase.table("epi_drug_candidates").select("*").in_("name", DRUGS_TO_PROMOTE).execute()

    if not candidates.data:
        print("No candidates found to promote!")
        return

    # Group by drug
    drugs_data = {}
    for c in candidates.data:
        name = c["name"]
        if name not in drugs_data:
            drugs_data[name] = {
                "chembl_id": c.get("chembl_id") or c.get("ot_drug_id"),
                "ot_drug_id": c.get("ot_drug_id"),
                "drug_type": c.get("drug_type"),
                "max_phase": c.get("max_clinical_phase"),
                "targets": set(),
                "target_mechanisms": {},
                "indications": {},  # efo_id -> name
            }
        drugs_data[name]["targets"].add(c["source_target_symbol"])
        if c.get("mechanism_of_action"):
            drugs_data[name]["target_mechanisms"][c["source_target_symbol"]] = c["mechanism_of_action"]
        if c.get("indication_efo_id"):
            drugs_data[name]["indications"][c["indication_efo_id"]] = c.get("indication_name")

    print(f"Found {len(drugs_data)} drugs to promote:")
    for name, data in drugs_data.items():
        print(f"  - {name}: {len(data['targets'])} targets, {len(data['indications'])} indications")
    print()

    # Promote each drug
    for name, data in drugs_data.items():
        print(f"Processing {name}...")

        # 1. Insert into epi_drugs
        drug_record = {
            "name": name,
            "chembl_id": data["chembl_id"],
            "ot_drug_id": data["ot_drug_id"],
            "drug_type": data["drug_type"],
            "fda_approved": False,  # Pipeline drug
            "source": "open_targets",
        }

        # Check if already exists
        existing = supabase.table("epi_drugs").select("id").eq("name", name).execute()
        if existing.data:
            drug_id = existing.data[0]["id"]
            print(f"  Drug already exists with id {drug_id}")
        else:
            result = supabase.table("epi_drugs").insert(drug_record).execute()
            drug_id = result.data[0]["id"]
            print(f"  Created drug with id {drug_id}")

        # 2. Link to targets
        for target_symbol in data["targets"]:
            target = get_target_by_symbol(target_symbol)
            if not target:
                print(f"  Warning: Target {target_symbol} not found")
                continue

            # Check if link exists
            existing_link = supabase.table("epi_drug_targets").select("id").eq("drug_id", drug_id).eq("target_id", target["id"]).execute()
            if not existing_link.data:
                supabase.table("epi_drug_targets").insert({
                    "drug_id": drug_id,
                    "target_id": target["id"],
                    "mechanism_of_action": data["target_mechanisms"].get(target_symbol),
                    "is_primary_target": True,  # All targets from OT are considered primary
                }).execute()
                print(f"  Linked to target {target_symbol}")

        # 3. Link to indications and create scores
        for efo_id, ind_name in list(data["indications"].items())[:5]:  # Limit to top 5 indications
            if not ind_name:
                continue

            indication_id = get_or_create_indication(efo_id, ind_name)

            # Check if drug-indication link exists
            existing_di = supabase.table("epi_drug_indications").select("id").eq("drug_id", drug_id).eq("indication_id", indication_id).execute()
            if not existing_di.data:
                supabase.table("epi_drug_indications").insert({
                    "drug_id": drug_id,
                    "indication_id": indication_id,
                }).execute()

            # 4. Create score record
            existing_score = supabase.table("epi_scores").select("id").eq("drug_id", drug_id).eq("indication_id", indication_id).execute()
            if not existing_score.data:
                # Compute scores
                # Bio score based on phase
                phase = data["max_phase"] or 1
                bio_score = min(100, phase * 20 + 20)  # Phase 1=40, 2=60, 3=80, 4=100

                # Tractability score from first target
                tract_score = 50.0
                for target_symbol in data["targets"]:
                    target = get_target_by_symbol(target_symbol)
                    if target and target.get("ot_target_id"):
                        tract_score = compute_tractability_score(target["ot_target_id"])
                        break

                # Chem score placeholder (will be updated by ChEMBL pipeline)
                chem_score = 50.0

                # Total score
                total_score = 0.5 * bio_score + 0.3 * chem_score + 0.2 * tract_score

                supabase.table("epi_scores").insert({
                    "drug_id": drug_id,
                    "indication_id": indication_id,
                    "bio_score": bio_score,
                    "chem_score": chem_score,
                    "tractability_score": tract_score,
                    "total_score": total_score,
                }).execute()
                print(f"  Created score for {ind_name[:30]}: Bio={bio_score:.0f}, Tract={tract_score:.0f}, Total={total_score:.1f}")

        # 5. Mark candidates as promoted
        supabase.table("epi_drug_candidates").update({"status": "promoted"}).eq("name", name).execute()
        print(f"  Marked candidates as promoted")
        print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    drugs = supabase.table("epi_drugs").select("id, name, fda_approved", count="exact").execute()
    scores = supabase.table("epi_scores").select("id", count="exact").execute()

    print(f"Total drugs: {drugs.count}")
    print(f"  - FDA Approved: {len([d for d in drugs.data if d['fda_approved']])}")
    print(f"  - Pipeline: {len([d for d in drugs.data if not d['fda_approved']])}")
    print(f"Total scored drug-indication pairs: {scores.count}")


if __name__ == "__main__":
    main()
