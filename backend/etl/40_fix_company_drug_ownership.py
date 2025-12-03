"""
40_fix_company_drug_ownership.py

Fixes drug-company ownership discrepancies identified in fact-check audit.
Based on verification against FDA records, company press releases, and SEC filings.

Discrepancies Fixed:
1. IDH inhibitors (ivosidenib, vorasidenib, enasidenib) -> Servier (not Agios)
2. Olutasidenib -> Rigel Pharmaceuticals (not Agios/Forma)
3. Belinostat -> Acrotech Biopharma (not Spectrum)
4. Decitabine -> Otsuka (US) / Janssen (EU) (not BMS)
5. Pelabresib -> Novartis via MorphoSys acquisition
6. Company status updates for acquired/bankrupt companies

Sources:
- https://servier.com/wp-content/uploads/2022/11/servier-completes-acquisition-agios-oncology-business_PR.pdf
- https://www.otsuka-us.com/news/otsuka-acquires-rights-hematological-cancer-treatment-dacogenr-decitabine-eisai-us
- https://www.novartis.com/news/media-releases/novartis-strengthen-oncology-pipeline-agreement-acquire-morphosys-ag-eur-68-share-or-aggregate-eur-27bn-cash
- https://beleodaq.com/

Run: python -m backend.etl.40_fix_company_drug_ownership
"""

import os
import sys
from datetime import date

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from supabase import create_client

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL", "https://fhwvmhgqxqtflbctogtq.supabase.co")
key = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZod3ZtaGdxeHF0ZmxiY3RvZ3RxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM3NTYxOTUsImV4cCI6MjA3OTMzMjE5NX0.IaDKmGm63gmv7c2QSMjBYgsq_bKl-uMv3QG95ndCD_g")
supabase = create_client(url, key)


# ============================================================
# NEW COMPANIES TO ADD
# ============================================================
NEW_COMPANIES = [
    {
        "name": "Servier",
        "ticker": None,  # Private French company
        "exchange": None,
        "description": "French pharmaceutical company. Acquired Agios oncology portfolio in April 2021 including ivosidenib, vorasidenib, and enasidenib.",
        "website": "https://www.servier.com",
        "is_pure_play_epi": False,
        "epi_focus_score": 40,
        "headquarters": "Suresnes, France",
    },
    {
        "name": "Rigel Pharmaceuticals",
        "ticker": "RIGL",
        "exchange": "NASDAQ",
        "description": "Biotechnology company focused on hematology-oncology. Licensed olutasidenib from Forma Therapeutics in August 2022.",
        "website": "https://www.rigel.com",
        "is_pure_play_epi": False,
        "epi_focus_score": 30,
        "headquarters": "South San Francisco, CA",
    },
    {
        "name": "Acrotech Biopharma",
        "ticker": None,  # Subsidiary of Aurobindo
        "exchange": None,
        "description": "Subsidiary of Aurobindo Pharma. Acquired belinostat (Beleodaq) and other oncology drugs from Spectrum Pharmaceuticals in March 2019.",
        "website": "https://www.acrotechbiopharma.com",
        "is_pure_play_epi": False,
        "epi_focus_score": 25,
        "headquarters": "East Windsor, NJ",
    },
    {
        "name": "Otsuka Pharmaceutical",
        "ticker": "4578.T",
        "exchange": "Tokyo Stock Exchange",
        "description": "Japanese pharmaceutical company. Acquired US/Canada/Japan rights to decitabine (Dacogen) from Eisai in 2014.",
        "website": "https://www.otsuka.com",
        "is_pure_play_epi": False,
        "epi_focus_score": 15,
        "headquarters": "Tokyo, Japan",
    },
]


# ============================================================
# DRUG OWNERSHIP CORRECTIONS
# Key: drug name -> list of correct owners with roles
# ============================================================
DRUG_OWNERSHIP_FIXES = {
    # IDH inhibitors - Servier acquired from Agios in 2021
    "IVOSIDENIB": [
        {"company": "Servier", "role": "owner", "is_primary": True, "notes": "Acquired from Agios April 2021"},
        {"company": "Agios Pharmaceuticals", "role": "royalty_holder", "is_primary": False, "notes": "Retains royalty rights"},
    ],
    "VORASIDENIB": [
        {"company": "Servier", "role": "owner", "is_primary": True, "notes": "Acquired from Agios April 2021"},
        {"company": "Agios Pharmaceuticals", "role": "royalty_holder", "is_primary": False, "notes": "Sold royalty to Royalty Pharma"},
    ],
    "ENASIDENIB": [
        {"company": "Servier", "role": "owner", "is_primary": True, "notes": "Acquired from Agios April 2021"},
        {"company": "Bristol-Myers Squibb", "role": "co_promoter", "is_primary": False, "notes": "US co-promotion rights"},
    ],
    # Olutasidenib - Licensed to Rigel from Forma in Aug 2022
    "OLUTASIDENIB": [
        {"company": "Rigel Pharmaceuticals", "role": "licensee", "is_primary": True, "notes": "Licensed from Forma Aug 2022"},
    ],
    # Belinostat - Acrotech acquired from Spectrum in 2019
    "BELINOSTAT": [
        {"company": "Acrotech Biopharma", "role": "owner", "is_primary": True, "notes": "Acquired from Spectrum March 2019"},
    ],
    # Decitabine - Otsuka owns US rights, Janssen has EU/ROW
    "DECITABINE": [
        {"company": "Otsuka Pharmaceutical", "role": "owner", "is_primary": True, "notes": "US/Canada/Japan rights from Eisai 2014"},
        {"company": "Janssen", "role": "licensee", "is_primary": False, "notes": "EU/ROW commercialization rights"},
    ],
    # Pelabresib - Now Novartis via MorphoSys acquisition
    "PELABRESIB": [
        {"company": "Novartis", "role": "owner", "is_primary": True, "notes": "Via MorphoSys acquisition May 2024"},
        {"company": "MorphoSys", "role": "originator", "is_primary": False, "notes": "Acquired Constellation 2021, then acquired by Novartis 2024"},
    ],
}


# ============================================================
# COMPANY STATUS UPDATES
# ============================================================
COMPANY_STATUS_UPDATES = [
    {
        "name": "Forma Therapeutics",
        "status": "acquired",
        "acquirer": "Novo Nordisk A/S",
        "acquisition_date": "2022-10-14",
        "status_notes": "Acquired for $1.1B. Olutasidenib licensed to Rigel before acquisition.",
    },
    {
        "name": "Gilead Sciences",
        "remove_drug": "ENASIDENIB",
        "notes": "Gilead never owned enasidenib - this was an error in original data",
    },
]


def get_or_create_company(company_data: dict) -> str | None:
    """Get existing company by name or create new one."""
    name = company_data["name"]

    # Check if exists
    result = supabase.table("epi_companies").select("id").eq("name", name).execute()
    if result.data:
        print(f"  Found existing company: {name}")
        return result.data[0]["id"]

    # Create new
    print(f"  Creating new company: {name}")
    result = supabase.table("epi_companies").insert(company_data).execute()
    if result.data:
        return result.data[0]["id"]
    return None


def get_drug_by_name(drug_name: str) -> dict | None:
    """Get drug by name."""
    result = supabase.table("epi_drugs").select("id, name").ilike("name", drug_name).execute()
    if result.data:
        return result.data[0]
    return None


def get_company_by_name(company_name: str) -> dict | None:
    """Get company by name."""
    result = supabase.table("epi_companies").select("id, name").eq("name", company_name).execute()
    if result.data:
        return result.data[0]
    return None


def clear_drug_company_links(drug_id: str):
    """Remove all existing drug-company links for a drug."""
    supabase.table("epi_drug_companies").delete().eq("drug_id", drug_id).execute()


def create_drug_company_link(drug_id: str, company_id: str, role: str, is_primary: bool):
    """Create a drug-company relationship."""
    data = {
        "drug_id": drug_id,
        "company_id": company_id,
        "role": role,
        "is_primary": is_primary,
    }
    try:
        supabase.table("epi_drug_companies").upsert(
            data,
            on_conflict="drug_id,company_id,role"
        ).execute()
        return True
    except Exception as e:
        print(f"    ERROR creating link: {e}")
        return False


def update_company_status(name: str, updates: dict):
    """Update company status fields."""
    supabase.table("epi_companies").update(updates).eq("name", name).execute()


def run():
    print("=" * 70)
    print("40_fix_company_drug_ownership.py")
    print("Fixing Drug-Company Ownership Based on Fact-Check Audit")
    print("=" * 70)

    # ============================================================
    # STEP 1: Add new companies
    # ============================================================
    print("\n" + "-" * 50)
    print("STEP 1: Adding Missing Companies")
    print("-" * 50)

    new_company_ids = {}
    for company_data in NEW_COMPANIES:
        company_id = get_or_create_company(company_data)
        if company_id:
            new_company_ids[company_data["name"]] = company_id
            print(f"  ✓ {company_data['name']}: {company_id[:8]}...")
        else:
            print(f"  ✗ Failed to add: {company_data['name']}")

    # ============================================================
    # STEP 2: Fix drug-company relationships
    # ============================================================
    print("\n" + "-" * 50)
    print("STEP 2: Fixing Drug-Company Relationships")
    print("-" * 50)

    fixed_count = 0
    for drug_name, owners in DRUG_OWNERSHIP_FIXES.items():
        print(f"\n  Processing: {drug_name}")

        drug = get_drug_by_name(drug_name)
        if not drug:
            print(f"    WARN: Drug not found in database")
            continue

        # Clear existing links
        clear_drug_company_links(drug["id"])
        print(f"    Cleared existing relationships")

        # Create new correct links
        for owner_info in owners:
            company = get_company_by_name(owner_info["company"])
            if not company:
                print(f"    WARN: Company not found: {owner_info['company']}")
                continue

            success = create_drug_company_link(
                drug["id"],
                company["id"],
                owner_info["role"],
                owner_info["is_primary"]
            )
            if success:
                print(f"    ✓ Linked to {owner_info['company']} (role: {owner_info['role']})")
                fixed_count += 1

    # ============================================================
    # STEP 3: Update company statuses
    # ============================================================
    print("\n" + "-" * 50)
    print("STEP 3: Updating Company Statuses")
    print("-" * 50)

    for update in COMPANY_STATUS_UPDATES:
        name = update["name"]

        if "remove_drug" in update:
            # Remove incorrect drug link
            drug = get_drug_by_name(update["remove_drug"])
            company = get_company_by_name(name)
            if drug and company:
                supabase.table("epi_drug_companies").delete().eq("drug_id", drug["id"]).eq("company_id", company["id"]).execute()
                print(f"  ✓ Removed {update['remove_drug']} from {name}")
        else:
            # Update status
            status_updates = {
                "status": update.get("status"),
                "acquirer": update.get("acquirer"),
                "acquisition_date": update.get("acquisition_date"),
                "status_notes": update.get("status_notes"),
            }
            # Remove None values
            status_updates = {k: v for k, v in status_updates.items() if v is not None}

            update_company_status(name, status_updates)
            print(f"  ✓ Updated {name}: status={update.get('status')}, acquirer={update.get('acquirer')}")

    # ============================================================
    # STEP 4: Verify and summarize
    # ============================================================
    print("\n" + "-" * 50)
    print("STEP 4: Verification Summary")
    print("-" * 50)

    # Count relationships
    result = supabase.table("epi_drug_companies").select("*, epi_drugs(name), epi_companies(name)").execute()
    print(f"\n  Total drug-company relationships: {len(result.data)}")

    # Show updated drugs
    print("\n  Updated drug ownerships:")
    for drug_name in DRUG_OWNERSHIP_FIXES.keys():
        drug = get_drug_by_name(drug_name)
        if drug:
            links = supabase.table("epi_drug_companies").select("*, epi_companies(name)").eq("drug_id", drug["id"]).execute()
            owners = [f"{l['epi_companies']['name']} ({l['role']})" for l in links.data]
            print(f"    {drug_name}: {', '.join(owners)}")

    print("\n" + "=" * 70)
    print(f"DONE: Fixed {fixed_count} drug-company relationships")
    print(f"      Added {len(new_company_ids)} new companies")
    print("=" * 70)


if __name__ == "__main__":
    run()
