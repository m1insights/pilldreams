"""
43_add_missing_target_drugs.py

Adds missing drugs for orphan targets based on Perplexity fact-check research.
Many targets in our database have NO drugs associated with them.

Key findings:
- 50 out of 79 targets have NO drugs linked
- Missing clinical-stage drugs for: EP300/CBP, SIRT1, G9a, KDM6, NSD2, KDM4, PRMT1

Sources:
- PubMed clinical trial publications
- ClinicalTrials.gov
- NCI Drug Dictionary
- Company press releases

Run: python -m backend.etl.43_add_missing_target_drugs
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from supabase import create_client

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL", "https://fhwvmhgqxqtflbctogtq.supabase.co")
key = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZod3ZtaGdxeHF0ZmxiY3RvZ3RxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM3NTYxOTUsImV4cCI6MjA3OTMzMjE5NX0.IaDKmGm63gmv7c2QSMjBYgsq_bKl-uMv3QG95ndCD_g")
supabase = create_client(url, key)


# ============================================================
# NEW DRUGS TO ADD
# Format: name -> (chembl_id, max_phase, fda_approved, source)
# ============================================================
NEW_DRUGS = {
    # EP300/CBP inhibitors (HAT)
    "INOBRODIB": ("CHEMBL4594323", 2, False, "CellCentric - EP300/CBP bromodomain inhibitor. Phase 2 for AML, myeloma, prostate cancer."),

    # SIRT1 inhibitors
    "SELISISTAT": ("CHEMBL502835", 3, False, "Siena Biotech - SIRT1 inhibitor. Phase 3 for Huntington's disease, preclinical for cancer."),

    # G9a/EHMT2 inhibitors (HMT)
    "UNC0642": ("CHEMBL3545307", 0, False, "Research tool - G9a inhibitor with improved PK for in vivo studies."),

    # KDM6A/KDM6B inhibitors
    "GSK-J4": ("CHEMBL3301603", 0, False, "Research tool - KDM6A/KDM6B dual inhibitor. Preclinical for AML, colorectal cancer."),

    # NSD2 inhibitors (HMT)
    "KTX-1001": (None, 1, False, "Kronos Bio - Selective NSD2 inhibitor. Phase 1 for relapsed/refractory multiple myeloma."),

    # KDM4 inhibitors
    "QC6352": ("CHEMBL4078028", 0, False, "Celgene - Selective KDM4 inhibitor. Preclinical for renal cancer."),

    # PRMT1 inhibitors (Type I PRMT)
    "GSK3368715": ("CHEMBL4520046", 1, False, "GSK - Type I PRMT inhibitor. Phase 1 terminated due to thromboembolic events."),
}


# ============================================================
# DRUG-TARGET LINKS TO ADD
# Format: drug_name -> [(target_symbol, mechanism)]
# ============================================================
DRUG_TARGET_LINKS = {
    # EP300/CBP
    "INOBRODIB": [
        ("EP300", "inhibitor"),
        # Note: CREBBP/CBP not in our targets list currently
    ],

    # SIRT1
    "SELISISTAT": [
        # Note: SIRT1 is not in our targets list - only SIRT2-7
        # We'll need to add SIRT1 or link to existing SIRTs
    ],

    # G9a/EHMT2
    "UNC0642": [
        ("EHMT2", "inhibitor"),
    ],

    # KDM6
    "GSK-J4": [
        ("KDM6A", "inhibitor"),
        ("KDM6B", "inhibitor"),
    ],

    # NSD2
    "KTX-1001": [
        ("NSD2", "inhibitor"),
    ],

    # KDM4
    "QC6352": [
        ("KDM4A", "inhibitor"),
        ("KDM4B", "inhibitor"),
        ("KDM4C", "inhibitor"),
    ],

    # PRMT1
    "GSK3368715": [
        ("PRMT1", "inhibitor"),
    ],

    # Update existing drug: VALEMETOSTAT should link to EZH1 too
    "VALEMETOSTAT": [
        ("EZH1", "inhibitor"),
        # EZH2 link should already exist
    ],
}


def get_or_create_drug(name, chembl_id, max_phase, fda_approved, source):
    """Get existing drug or create new one"""
    result = supabase.table("epi_drugs").select("id, name").ilike("name", name).execute()

    if result.data:
        return result.data[0]["id"], False  # exists

    # Create new drug
    drug_data = {
        "name": name,
        "max_phase": max_phase,
        "fda_approved": fda_approved,
        "source": source,
    }
    if chembl_id:
        drug_data["chembl_id"] = chembl_id

    result = supabase.table("epi_drugs").insert(drug_data).execute()
    return result.data[0]["id"], True  # created


def get_target_id(symbol):
    """Get target ID by symbol"""
    result = supabase.table("epi_targets").select("id").eq("symbol", symbol).execute()
    if result.data:
        return result.data[0]["id"]
    return None


def link_exists(drug_id, target_id):
    """Check if drug-target link exists"""
    result = supabase.table("epi_drug_targets").select("id").eq("drug_id", drug_id).eq("target_id", target_id).execute()
    return len(result.data) > 0


def run():
    print("=" * 70)
    print("43_add_missing_target_drugs.py")
    print("Adding Missing Drugs for Orphan Targets")
    print("=" * 70)

    # Step 1: Add new drugs
    print("\n--- Step 1: Adding new drugs ---")
    drugs_added = 0
    drug_ids = {}

    for name, (chembl_id, max_phase, fda_approved, source) in NEW_DRUGS.items():
        drug_id, created = get_or_create_drug(name, chembl_id, max_phase, fda_approved, source)
        drug_ids[name] = drug_id
        if created:
            print(f"  ✓ Created: {name} (Phase {max_phase})")
            drugs_added += 1
        else:
            print(f"  - Exists: {name}")

    # Step 2: Add drug-target links
    print("\n--- Step 2: Adding drug-target links ---")
    links_added = 0
    targets_not_found = []

    for drug_name, targets in DRUG_TARGET_LINKS.items():
        print(f"\nProcessing: {drug_name}")

        # Get drug ID
        result = supabase.table("epi_drugs").select("id").ilike("name", drug_name).execute()
        if not result.data:
            print(f"  ⚠ Drug not found: {drug_name}")
            continue
        drug_id = result.data[0]["id"]

        for target_symbol, mechanism in targets:
            target_id = get_target_id(target_symbol)
            if not target_id:
                print(f"  ⚠ Target not found: {target_symbol}")
                if target_symbol not in targets_not_found:
                    targets_not_found.append(target_symbol)
                continue

            if link_exists(drug_id, target_id):
                print(f"  - {target_symbol}: already linked")
                continue

            # Create link
            link_data = {
                "drug_id": drug_id,
                "target_id": target_id,
                "mechanism_of_action": mechanism,
                "is_primary_target": True,
            }
            try:
                supabase.table("epi_drug_targets").insert(link_data).execute()
                print(f"  ✓ {target_symbol}: LINKED ({mechanism})")
                links_added += 1
            except Exception as e:
                print(f"  ✗ {target_symbol}: Error - {e}")

    # Step 3: Summary
    print("\n" + "=" * 70)
    print(f"DONE: Added {drugs_added} new drugs")
    print(f"      Added {links_added} drug-target links")
    if targets_not_found:
        print(f"      Targets not in database: {', '.join(targets_not_found)}")
    print("=" * 70)

    # Step 4: Verification - targets that now have drugs
    print("\n--- Verification: Previously Orphan Targets ---")

    targets_to_check = ["EP300", "EHMT2", "KDM6A", "KDM6B", "NSD2", "KDM4A", "PRMT1", "EZH1"]

    for symbol in targets_to_check:
        target_result = supabase.table("epi_targets").select("id, symbol").eq("symbol", symbol).execute()
        if not target_result.data:
            print(f"  ⚠ {symbol}: Target not in database")
            continue

        target_id = target_result.data[0]["id"]
        links_result = supabase.table("epi_drug_targets").select(
            "epi_drugs(name)"
        ).eq("target_id", target_id).execute()

        drug_names = [r["epi_drugs"]["name"] for r in links_result.data if r.get("epi_drugs")]
        status = "✓" if drug_names else "✗"
        print(f"  {status} {symbol}: {len(drug_names)} drugs - {', '.join(drug_names[:3])}")


if __name__ == "__main__":
    run()
