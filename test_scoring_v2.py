import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.main import run_pipeline_etl
from backend.etl import supabase_client

def test_scoring_v2():
    load_dotenv()
    if not supabase_client.supabase:
        print("Supabase client not initialized.")
        return

    print("🚀 Starting Scoring V2 ETL Test...")
    try:
        # Run pipeline ETL
        run_pipeline_etl()
        print("✅ Pipeline ETL complete.")
        
        # Verify scores
        assets = supabase_client.supabase.table("pipeline_assets").select("*").limit(5).execute().data
        for asset in assets:
            print(f"Asset: {asset['name']}")
            print(f"  BioScore: {asset.get('bio_score')}")
            print(f"  ChemScore: {asset.get('chem_score')}")
            print(f"  TractScore: {asset.get('tractability_score')}")
            print(f"  TotalScore: {asset.get('total_score')}")
            print("-" * 20)
        
    except Exception as e:
        print(f"❌ Error in Scoring V2 ETL: {e}")

if __name__ == "__main__":
    test_scoring_v2()
