import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.etl import supabase_client

def check_chembl():
    load_dotenv()
    if not supabase_client.supabase:
        print("Supabase client not initialized.")
        return

    try:
        count = supabase_client.supabase.table("chembl_metrics").select("count", count="exact").execute().count
        print(f"ChEMBL Metrics Count: {count}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_chembl()
