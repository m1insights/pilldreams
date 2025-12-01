"""
13_seed_companies.py

Seeds epi_companies table and creates drug-company mappings.
Also links editing assets to their sponsor companies.

Run: python -m backend.etl.13_seed_companies
"""

import csv
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from backend.etl import supabase_client


def run():
    print("=" * 60)
    print("13_seed_companies.py")
    print("Seeding Companies and Drug Mappings")
    print("=" * 60)

    csv_path = os.path.join(os.path.dirname(__file__), "seed_epi_companies.csv")

    if not os.path.exists(csv_path):
        print(f"  ERROR: CSV file not found: {csv_path}")
        return

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Found {len(rows)} companies in seed file.\n")

    company_success = 0
    drug_links = 0
    editing_links = 0

    for row in rows:
        name = row.get("name", "").strip()
        if not name:
            continue

        print(f"Processing: {name}")

        # Build company data
        company_data = {
            "name": name,
            "ticker": row.get("ticker", "").strip() or None,
            "exchange": row.get("exchange", "").strip() or None,
            "description": row.get("description", "").strip() or None,
            "website": row.get("website", "").strip() or None,
            "is_pure_play_epi": row.get("is_pure_play_epi", "").upper() == "TRUE",
            "epi_focus_score": float(row.get("epi_focus_score", 0) or 0),
        }

        try:
            company_id = supabase_client.upsert_company(company_data)
            if company_id:
                print(f"  Upserted company: {name} (ID: {company_id[:8]}...)")
                company_success += 1

                # Link drugs
                drugs_str = row.get("drugs", "").strip()
                if drugs_str:
                    drug_names = [d.strip() for d in drugs_str.split(",") if d.strip()]
                    for drug_name in drug_names:
                        drug = supabase_client.get_drug_by_name(drug_name)
                        if drug:
                            supabase_client.insert_drug_company({
                                "drug_id": drug["id"],
                                "company_id": company_id,
                                "role": "originator",
                                "is_primary": True,
                            })
                            print(f"    Linked drug: {drug_name}")
                            drug_links += 1
                        else:
                            print(f"    WARN: Drug not found: {drug_name}")

                # Link editing assets by sponsor name
                editing_assets = supabase_client.get_editing_asset_by_sponsor(name)
                for asset in editing_assets:
                    supabase_client.insert_editing_asset_company({
                        "editing_asset_id": asset["id"],
                        "company_id": company_id,
                        "role": "originator",
                        "is_primary": True,
                    })
                    print(f"    Linked editing asset: {asset['name']}")
                    editing_links += 1

            else:
                print(f"  WARN: Could not upsert {name}")
        except Exception as e:
            print(f"  ERROR: {e}")

    print("\n" + "=" * 60)
    print(f"DONE: {company_success} companies seeded")
    print(f"      {drug_links} drug-company links created")
    print(f"      {editing_links} editing-company links created")
    print("=" * 60)


if __name__ == "__main__":
    run()
