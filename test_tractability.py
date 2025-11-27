import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.main import run_pipeline_etl
from backend.etl import supabase_client

def test_tractability():
    load_dotenv()
    if not supabase_client.supabase:
        print("Supabase client not initialized.")
        return

    print("🚀 Starting Tractability ETL Test...")
    try:
        # Run pipeline ETL (which now includes tractability)
        run_pipeline_etl()
        print("✅ Pipeline ETL complete.")
        
        # Verify metrics
        count = supabase_client.supabase.table("target_biology_metrics").select("count", count="exact").execute().count
        print(f"✅ Target Biology Metrics Count: {count}")
        
        # Check a sample
        sample = supabase_client.supabase.table("target_biology_metrics").select("*").limit(1).execute()
        if sample.data:
            print(f"Sample Data: {sample.data[0]}")
        
    except Exception as e:
        print(f"❌ Error in Tractability ETL: {e}")

if __name__ == "__main__":
    test_tractability()
