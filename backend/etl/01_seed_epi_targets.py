import csv
import os
import sys
from backend.etl import open_targets, supabase_client

# Ensure we can import backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

def run():
    print("🌱 Seeding Epigenetic Targets...")
    
    csv_path = os.path.join(os.path.dirname(__file__), "seed_epi_targets.csv")
    
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        targets = list(reader)
        
    print(f"Found {len(targets)} targets in seed file.")
    
    for row in targets:
        symbol = row["symbol"]
        print(f"Processing {symbol}...")
        
        # 1. Search Open Targets for ID
        ot_target = open_targets.search_target_by_symbol(symbol)
        
        if not ot_target:
            print(f"  ❌ Could not find target for {symbol} in Open Targets.")
            continue
            
        ot_id = ot_target["id"]
        
        # 2. Fetch details (UniProt ID)
        details = open_targets.fetch_target_details(ot_id)
        uniprot_id = None
        if details.get("proteinAnnotations"):
             uniprot_id = details["proteinAnnotations"]["id"]
        
        # 3. Upsert into DB
        epi_target_data = {
            "symbol": symbol,
            "full_name": row.get("full_name") or ot_target.get("approvedName"), # Search hit has approvedName?
            "family": row["family"],
            "class": row["class"],
            "ensembl_id": ot_id,
            "ot_target_id": ot_id,
            "uniprot_id": uniprot_id,
            "is_core_epigenetic": row["is_core_epigenetic"] == "TRUE"
        }
        
        target_id = supabase_client.upsert_epi_target(epi_target_data)
        if target_id:
            print(f"  ✅ Upserted {symbol} (ID: {target_id})")
        else:
            print(f"  ❌ Failed to upsert {symbol}")

if __name__ == "__main__":
    run()
