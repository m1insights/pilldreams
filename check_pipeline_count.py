import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.etl import supabase_client

def check_pipeline_counts():
    load_dotenv()
    if not supabase_client.supabase:
        print("Supabase client not initialized.")
        return

    try:
        response = supabase_client.supabase.table("pipeline_assets").select("count", count="exact").execute()
        print(f"Pipeline Assets: {response.count}")
    except Exception as e:
        print(f"Error checking pipeline assets: {e}")

if __name__ == "__main__":
    check_pipeline_counts()
