import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.main import run_full_etl
from backend.etl import supabase_client

def test_gold_chembl():
    load_dotenv()
    if not supabase_client.supabase:
        print("Supabase client not initialized.")
        return

    print("🚀 Starting Gold Set ChEMBL ETL Test...")
    try:
        # We only want to run for one disease to be fast
        # But run_full_etl iterates all. 
        # We can mock config.DISEASE_SCOPE or just let it run for the first one and kill it?
        # Or just run it, it shouldn't take too long for Gold Set (250 drugs).
        run_full_etl()
        print("✅ Gold Set ETL complete.")
        
        # Verify metrics linked to drug_id
        count = supabase_client.supabase.table("chembl_metrics").select("count", count="exact").not_.is_("drug_id", "null").execute().count
        print(f"✅ Gold Set ChEMBL Metrics Count: {count}")
        
    except Exception as e:
        print(f"❌ Error in Gold Set ETL: {e}")

if __name__ == "__main__":
    test_gold_chembl()
