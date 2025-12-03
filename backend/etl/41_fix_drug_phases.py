"""
41_fix_drug_phases.py

Fixes drug max_phase values based on FDA approval status verification.
Updates NULL phases and corrects FDA-approved drugs that should show max_phase=4.

Key principle: max_phase should reflect the HIGHEST phase the drug has reached,
not the current active trials. A Phase 4 (approved) drug may still have Phase 1
trials for new indications, but max_phase should still be 4.

Sources:
- FDA Drugs@FDA database
- Drugs.com approval history
- Company press releases

Run: python -m backend.etl.41_fix_drug_phases
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
# PHASE CORRECTIONS
# Format: drug_name -> (max_phase, fda_approved, notes)
# ============================================================
PHASE_CORRECTIONS = {
    # FDA-APPROVED DRUGS (Phase 4) - currently showing NULL
    "INCLISIRAN SODIUM": (4, True, "FDA approved Dec 2021 (Leqvio) - siRNA PCSK9 inhibitor"),
    "EVOLOCUMAB": (4, True, "FDA approved Aug 2015 (Repatha) - PCSK9 antibody"),
    "ALIROCUMAB": (4, True, "FDA approved July 2015 (Praluent) - PCSK9 antibody"),
    "PATISIRAN SODIUM": (4, True, "FDA approved Aug 2018 (Onpattro) - first RNAi therapeutic"),
    "INOTERSEN SODIUM": (4, True, "FDA approved Oct 2018 (Tegsedi) - antisense oligonucleotide for hATTR"),
    "VUTRISIRAN SODIUM": (4, True, "FDA approved June 2022 (Amvuttra) - siRNA for hATTR"),
    "TAFAMIDIS MEGLUMINE": (4, True, "FDA approved May 2019 (Vyndaqel) - TTR stabilizer for ATTR-CM"),
    "EPLONTERSEN": (4, True, "FDA approved Dec 2023 (Wainua) - antisense for hATTR polyneuropathy"),
    "ACORAMIDIS": (4, True, "FDA approved Nov 2024 (Attruby) - TTR stabilizer for ATTR-CM"),

    # PHASE 3 DRUGS - update based on current trials
    "PELABRESIB": (3, False, "Phase 3 MANIFEST-2 completed. Under Novartis review. Not yet approved."),
    "APABETALONE": (3, False, "Phase 3 BETonMACE completed. BET inhibitor for CVD."),

    # RESEARCH TOOLS / DISCONTINUED - should not have clinical phase
    "JQ1": (0, False, "Research tool compound, never entered clinical trials"),

    # DISCONTINUED / TERMINATED
    "BOCOCIZUMAB": (3, False, "Phase 3 SPIRE trials - development discontinued by Pfizer 2016"),
    "REVUSIRAN": (3, False, "Phase 3 ENDEAVOUR - discontinued due to safety concerns 2016"),

    # Other drugs that need phase updates from ChEMBL data
    "SRT-2104": (2, False, "Phase 2 trials for metabolic diseases - SIRT1 activator"),
    "EDIFOLIGIDE SODIUM": (3, False, "Phase 3 PREVENT trials - E2F decoy, development discontinued"),
    "RALPANCIZUMAB": (1, False, "Phase 1 - discontinued PCSK9 antibody"),
    "FROVOCIMAB": (2, False, "Phase 2 - PCSK9 antibody in development"),
    "LERODALCIBEP": (3, False, "Phase 3 - oral PCSK9 inhibitor"),
    "ONGERICIMAB": (2, False, "Phase 2 - PCSK9 antibody"),
    "TAFOLECIMAB": (3, False, "Phase 3 trials in China - PCSK9 antibody"),
}


def run():
    print("=" * 70)
    print("41_fix_drug_phases.py")
    print("Fixing Drug Phase Values Based on FDA Approval Verification")
    print("=" * 70)

    updated_count = 0
    not_found = []

    for drug_name, (max_phase, fda_approved, notes) in PHASE_CORRECTIONS.items():
        print(f"\nProcessing: {drug_name}")
        print(f"  Target: max_phase={max_phase}, fda_approved={fda_approved}")
        print(f"  Notes: {notes}")

        # Find the drug
        result = supabase.table("epi_drugs").select("id, name, max_phase, fda_approved").ilike("name", drug_name).execute()

        if not result.data:
            print(f"  ⚠ Drug not found in database")
            not_found.append(drug_name)
            continue

        drug = result.data[0]
        current_phase = drug.get("max_phase")
        current_fda = drug.get("fda_approved", False)

        # Check if update needed
        if current_phase == max_phase and current_fda == fda_approved:
            print(f"  ✓ Already correct (phase={current_phase}, fda={current_fda})")
            continue

        # Update the drug
        update_data = {
            "max_phase": max_phase,
            "fda_approved": fda_approved,
        }

        try:
            supabase.table("epi_drugs").update(update_data).eq("id", drug["id"]).execute()
            print(f"  ✓ Updated: phase {current_phase} → {max_phase}, fda {current_fda} → {fda_approved}")
            updated_count += 1
        except Exception as e:
            print(f"  ✗ Error updating: {e}")

    # ============================================================
    # STEP 2: Auto-fix any drugs marked fda_approved=True but max_phase != 4
    # ============================================================
    print("\n" + "-" * 50)
    print("STEP 2: Auto-fixing FDA approved drugs with wrong phase")
    print("-" * 50)

    result = supabase.table("epi_drugs").select("id, name, max_phase, fda_approved").eq("fda_approved", True).neq("max_phase", 4).execute()

    for drug in result.data:
        print(f"\n  {drug['name']}: fda_approved=True but max_phase={drug['max_phase']}")
        try:
            supabase.table("epi_drugs").update({"max_phase": 4}).eq("id", drug["id"]).execute()
            print(f"    ✓ Fixed: max_phase → 4")
            updated_count += 1
        except Exception as e:
            print(f"    ✗ Error: {e}")

    # ============================================================
    # STEP 3: Summary
    # ============================================================
    print("\n" + "=" * 70)
    print(f"DONE: Updated {updated_count} drug records")
    if not_found:
        print(f"      Drugs not found: {', '.join(not_found)}")
    print("=" * 70)

    # Print verification
    print("\n--- Verification: All FDA-approved drugs ---")
    result = supabase.table("epi_drugs").select("name, max_phase, fda_approved").eq("fda_approved", True).order("name").execute()
    for drug in result.data:
        phase_ok = "✓" if drug["max_phase"] == 4 else "✗"
        print(f"  {phase_ok} {drug['name']}: phase={drug['max_phase']}")


if __name__ == "__main__":
    run()
