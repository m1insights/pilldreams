"""
42_fix_drug_indications.py

Fixes drug-indication relationships based on FDA approval verification.
Adds missing indication links for FDA-approved drugs.

Key findings from Perplexity fact-check:
1. 8 FDA-approved drugs have NO INDICATIONS LINKED in database
2. PCSK9 inhibitors: Hypercholesterolemia (HeFH, HoFH, ASCVD)
3. TTR drugs: ATTR Amyloidosis subtypes (ATTR-CM, hATTR-PN)

Sources:
- FDA Drugs@FDA database
- NCBI StatPearls PCSK9 Inhibitors
- Medscape TTR Amyloidosis Treatment Guide

Run: python -m backend.etl.42_fix_drug_indications
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
# INDICATION DEFINITIONS TO ADD
# Format: indication_name -> (efo_id, disease_area)
# ============================================================
NEW_INDICATIONS = {
    "ATTR Cardiomyopathy": ("Orphanet_85451", "Cardiology"),
    "Hereditary ATTR Polyneuropathy": ("Orphanet_85447", "Neurology"),
    "Heterozygous Familial Hypercholesterolemia": ("EFO_0004798", "Cardiology"),
    "Homozygous Familial Hypercholesterolemia": ("EFO_0004799", "Cardiology"),
    "ASCVD": ("EFO_0000378", "Cardiology"),
}


# ============================================================
# DRUG-INDICATION CORRECTIONS
# Format: drug_name -> [(indication_name, approval_status, approval_date, notes)]
# ============================================================
DRUG_INDICATION_FIXES = {
    # PCSK9 Inhibitors - FDA approved for hyperlipidemia/ASCVD
    "ALIROCUMAB": [
        ("Hypercholesterolemia", "approved", "2015-07-24", "FDA approved - Praluent for HeFH and ASCVD"),
        ("Heterozygous Familial Hypercholesterolemia", "approved", "2015-07-24", "Primary indication"),
        ("ASCVD", "approved", "2019-04-28", "CV risk reduction in established ASCVD"),
    ],
    "EVOLOCUMAB": [
        ("Hypercholesterolemia", "approved", "2015-08-27", "FDA approved - Repatha for HeFH, HoFH, ASCVD"),
        ("Heterozygous Familial Hypercholesterolemia", "approved", "2015-08-27", "Primary indication"),
        ("Homozygous Familial Hypercholesterolemia", "approved", "2015-08-27", "Also approved for HoFH (unlike alirocumab)"),
        ("ASCVD", "approved", "2017-12-01", "CV risk reduction in established ASCVD"),
    ],
    "INCLISIRAN SODIUM": [
        ("Hypercholesterolemia", "approved", "2021-12-22", "FDA approved - Leqvio for HeFH and ASCVD"),
        ("Heterozygous Familial Hypercholesterolemia", "approved", "2021-12-22", "Primary indication"),
        ("ASCVD", "approved", "2021-12-22", "CV risk reduction in established ASCVD"),
    ],

    # TTR Stabilizers - FDA approved for ATTR-CM
    "TAFAMIDIS MEGLUMINE": [
        ("ATTR Amyloidosis", "approved", "2019-05-03", "FDA approved - Vyndaqel for ATTR-CM"),
        ("ATTR Cardiomyopathy", "approved", "2019-05-03", "Primary indication - wild-type and hereditary ATTR-CM"),
    ],
    "ACORAMIDIS": [
        ("ATTR Amyloidosis", "approved", "2024-11-22", "FDA approved - Attruby for ATTR-CM"),
        ("ATTR Cardiomyopathy", "approved", "2024-11-22", "To reduce CV death and CV hospitalization"),
    ],

    # TTR Silencers (siRNA/ASO) - FDA approved for hATTR-PN and/or ATTR-CM
    "PATISIRAN SODIUM": [
        ("ATTR Amyloidosis", "approved", "2018-08-10", "FDA approved - Onpattro for hATTR-PN"),
        ("Hereditary ATTR Polyneuropathy", "approved", "2018-08-10", "First RNAi therapeutic approved by FDA"),
    ],
    "VUTRISIRAN SODIUM": [
        ("ATTR Amyloidosis", "approved", "2022-06-13", "FDA approved - Amvuttra for hATTR-PN, ATTR-CM (2025)"),
        ("Hereditary ATTR Polyneuropathy", "approved", "2022-06-13", "Initial approval for hATTR-PN"),
        ("ATTR Cardiomyopathy", "approved", "2025-03-21", "Expanded indication for ATTR-CM"),
    ],
    "INOTERSEN SODIUM": [
        ("ATTR Amyloidosis", "approved", "2018-10-05", "FDA approved - Tegsedi for hATTR-PN"),
        ("Hereditary ATTR Polyneuropathy", "approved", "2018-10-05", "With REMS program due to safety concerns"),
    ],
    "EPLONTERSEN": [
        ("ATTR Amyloidosis", "approved", "2023-12-21", "FDA approved - Wainua for hATTR-PN"),
        ("Hereditary ATTR Polyneuropathy", "approved", "2023-12-21", "First monthly self-administered ATTR therapy"),
        # Note: ATTR-CM indication is under Phase 3 trial, not yet approved
    ],
}


def ensure_indication_exists(name, efo_id, disease_area):
    """Add indication if it doesn't exist, return ID"""
    # Check if exists
    result = supabase.table("epi_indications").select("id, name").ilike("name", name).execute()

    if result.data:
        return result.data[0]["id"]

    # Create new indication
    new_ind = {
        "name": name,
        "efo_id": efo_id,
        "disease_area": disease_area,
    }
    result = supabase.table("epi_indications").insert(new_ind).execute()
    print(f"  ✓ Created indication: {name}")
    return result.data[0]["id"]


def get_drug_id(name):
    """Get drug ID by name"""
    result = supabase.table("epi_drugs").select("id, name").ilike("name", name).execute()
    if result.data:
        return result.data[0]["id"]
    return None


def get_indication_id(name):
    """Get indication ID by name"""
    result = supabase.table("epi_indications").select("id, name").ilike("name", name).execute()
    if result.data:
        return result.data[0]["id"]
    return None


def link_exists(drug_id, indication_id):
    """Check if drug-indication link already exists"""
    result = supabase.table("epi_drug_indications").select("id").eq("drug_id", drug_id).eq("indication_id", indication_id).execute()
    return len(result.data) > 0


def run():
    print("=" * 70)
    print("42_fix_drug_indications.py")
    print("Fixing Drug-Indication Relationships Based on FDA Verification")
    print("=" * 70)

    # Step 1: Ensure all new indications exist
    print("\n--- Step 1: Ensuring indications exist ---")
    for name, (efo_id, disease_area) in NEW_INDICATIONS.items():
        ensure_indication_exists(name, efo_id, disease_area)

    # Step 2: Add drug-indication links
    print("\n--- Step 2: Adding drug-indication links ---")
    added_count = 0
    skipped_count = 0
    not_found = []

    for drug_name, indications in DRUG_INDICATION_FIXES.items():
        print(f"\nProcessing: {drug_name}")

        drug_id = get_drug_id(drug_name)
        if not drug_id:
            print(f"  ⚠ Drug not found in database")
            not_found.append(drug_name)
            continue

        for ind_name, approval_status, approval_date, notes in indications:
            indication_id = get_indication_id(ind_name)
            if not indication_id:
                # Try to create if it's in our new indications
                if ind_name in NEW_INDICATIONS:
                    efo_id, desc = NEW_INDICATIONS[ind_name]
                    indication_id = ensure_indication_exists(ind_name, efo_id, desc)
                else:
                    print(f"  ⚠ Indication not found: {ind_name}")
                    continue

            if link_exists(drug_id, indication_id):
                print(f"  - {ind_name}: already linked")
                skipped_count += 1
                continue

            # Create the link (note: table uses drug_id/indication_id, not epi_ prefix)
            link_data = {
                "drug_id": drug_id,
                "indication_id": indication_id,
                "approval_status": approval_status,
                # Note: approval_date and notes columns don't exist in schema
            }

            try:
                supabase.table("epi_drug_indications").insert(link_data).execute()
                print(f"  ✓ {ind_name}: ADDED ({approval_status})")
                added_count += 1
            except Exception as e:
                print(f"  ✗ {ind_name}: Error - {e}")

    # Step 3: Summary
    print("\n" + "=" * 70)
    print(f"DONE: Added {added_count} drug-indication links")
    print(f"      Skipped {skipped_count} (already existed)")
    if not_found:
        print(f"      Drugs not found: {', '.join(not_found)}")
    print("=" * 70)

    # Step 4: Verification - show drugs with indications now
    print("\n--- Verification: FDA-Approved Drugs with Indications ---")

    drugs_to_check = list(DRUG_INDICATION_FIXES.keys())
    for drug_name in drugs_to_check:
        drug_result = supabase.table("epi_drugs").select("id, name, fda_approved").ilike("name", drug_name).execute()
        if not drug_result.data:
            continue

        drug = drug_result.data[0]
        drug_id = drug["id"]

        # Get indications
        ind_result = supabase.table("epi_drug_indications").select(
            "approval_status, epi_indications(name)"
        ).eq("drug_id", drug_id).execute()

        ind_names = [r["epi_indications"]["name"] for r in ind_result.data if r.get("epi_indications")]
        fda_mark = "✓" if drug.get("fda_approved") else "○"
        print(f"  {fda_mark} {drug['name']}: {len(ind_names)} indications")
        for ind_name in ind_names:
            print(f"      - {ind_name}")


if __name__ == "__main__":
    run()
