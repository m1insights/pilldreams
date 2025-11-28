"""
ETL Step 02: Seed Gold Set of Approved Epigenetic Drugs

Uses a CURATED seed file (seed_gold_drugs.csv) containing the ~12 FDA-approved
epigenetic oncology drugs. This replaces the previous Phase 4 filter which
pulled in thousands of irrelevant drugs.

Gold Criteria:
- FDA-approved (or major market approval)
- Primary mechanism is epigenetic (HDAC, DNMT, EZH2, IDH inhibition)
- Approved for oncology indication
"""

import csv
import os
import sys
from backend.etl import supabase_client

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))


def run():
    print("🏆 Seeding Gold Set (Curated Approved Epigenetic Drugs)...")

    if not supabase_client.supabase:
        print("❌ Supabase client not initialized.")
        return

    csv_path = os.path.join(os.path.dirname(__file__), "seed_gold_drugs.csv")

    if not os.path.exists(csv_path):
        print(f"❌ Seed file not found: {csv_path}")
        return

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        drugs = list(reader)

    print(f"Found {len(drugs)} curated gold drugs in seed file.")

    # Fetch all targets for linking
    targets = supabase_client.supabase.table("epi_targets").select("id, symbol").execute().data
    target_map = {t["symbol"]: t["id"] for t in targets}

    for row in drugs:
        name = row["name"]
        print(f"Processing {name}...")

        # 1. Upsert drug
        # Schema has: name, drug_type, chembl_id, ot_drug_id, fda_approved, first_approval_date, source
        approval_year = row.get("approval_year")
        first_approval_date = f"{approval_year}-01-01" if approval_year else None

        drug_data = {
            "name": name,
            "chembl_id": row.get("chembl_id"),
            "drug_type": row.get("drug_type"),
            "fda_approved": row.get("fda_approved", "").upper() == "TRUE",
            "first_approval_date": first_approval_date,
            "source": "Curated_Gold"
        }

        drug_id = supabase_client.upsert_epi_drug(drug_data)

        if not drug_id:
            print(f"  ❌ Failed to upsert {name}")
            continue

        print(f"  ✅ Upserted {name} (ID: {drug_id})")

        # 2. Link to primary target
        target_symbol = row.get("primary_target_symbol")
        if target_symbol and target_symbol in target_map:
            supabase_client.insert_epi_drug_target({
                "drug_id": drug_id,
                "target_id": target_map[target_symbol],
                "mechanism_of_action": row.get("mechanism"),
                "is_primary_target": True
            })
            print(f"     Linked to target: {target_symbol}")
        else:
            print(f"     ⚠️ Target {target_symbol} not found in database")

        # 3. Create indication entry
        indication_name = row.get("first_indication")
        if indication_name:
            indication_id = supabase_client.insert_epi_indication({
                "name": indication_name,
                "disease_area": "Oncology"
            })

            if indication_id:
                supabase_client.insert_epi_drug_indication({
                    "drug_id": drug_id,
                    "indication_id": indication_id,
                    "approval_status": "approved",
                    "max_phase": 4
                })
                print(f"     Linked to indication: {indication_name}")

    print(f"\n✅ Gold set seeding complete. {len(drugs)} drugs processed.")


if __name__ == "__main__":
    run()
