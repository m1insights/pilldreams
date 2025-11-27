import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.etl import supabase_client

def check_scores():
    load_dotenv()
    if not supabase_client.supabase:
        print("Supabase client not initialized.")
        return

    try:
        # Count total assets
        total = supabase_client.supabase.table("pipeline_assets").select("count", count="exact").execute().count
        
        # Count with score > 0
        scored = supabase_client.supabase.table("pipeline_assets").select("count", count="exact").gt("relative_score", 0).execute().count
        
        print(f"Total Assets: {total}")
        print(f"Assets with Score > 0: {scored}")
        print(f"Assets with Score = 0: {total - scored}")
        
    except Exception as e:
        print(f"Error checking scores: {e}")

if __name__ == "__main__":
    check_scores()
