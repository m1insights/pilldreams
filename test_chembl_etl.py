import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.main import run_pipeline_etl
from backend.etl import supabase_client

def test_chembl():
    load_dotenv()
    if not supabase_client.supabase:
        print("Supabase client not initialized.")
        return

    print("🚀 Starting ChEMBL ETL Test (Pipeline Assets Only)...")
    try:
        run_pipeline_etl()
        print("✅ Pipeline ETL complete.")
        
        # Verify metrics
        count = supabase_client.supabase.table("chembl_metrics").select("count", count="exact").execute().count
        print(f"✅ ChEMBL Metrics Count: {count}")
        
    except Exception as e:
        print(f"❌ Error in Pipeline ETL: {e}")

if __name__ == "__main__":
    test_chembl()
