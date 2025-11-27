import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.etl import supabase_client

def check_scoring():
    load_dotenv()
    if not supabase_client.supabase:
        print("Supabase client not initialized.")
        return

    try:
        # Fetch assets with non-null total_score
        assets = supabase_client.supabase.table("pipeline_assets").select("*").not_.is_("total_score", "null").limit(10).execute().data
        print(f"Assets with Total Score: {len(assets)}")
        for asset in assets:
            print(f"Asset: {asset['name']}")
            print(f"  Bio: {asset.get('bio_score')}")
            print(f"  Chem: {asset.get('chem_score')}")
            print(f"  Tract: {asset.get('tractability_score')}")
            print(f"  Total: {asset.get('total_score')}")
            print("-" * 20)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_scoring()
