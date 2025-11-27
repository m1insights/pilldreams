import os
import sys
from dotenv import load_dotenv
import json

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.etl import supabase_client

def fetch_example():
    load_dotenv()
    if not supabase_client.supabase:
        print("Supabase client not initialized.")
        return

    # Try to find a well-known drug
    drug_name = "FLUOXETINE" 
    
    # search for it
    response = supabase_client.supabase.table("drugs").select("*, drug_targets(*), drug_indications(*)").ilike("name", f"%{drug_name}%").limit(1).execute()
    
    if response.data:
        print(json.dumps(response.data[0], indent=2))
    else:
        print(f"Drug {drug_name} not found. Trying another...")
        # Fallback to just the first one with high pubmed count
        response = supabase_client.supabase.table("drugs").select("*, drug_targets(*), drug_indications(*)").gt("pubmed_count", 1000).limit(1).execute()
        if response.data:
            print(json.dumps(response.data[0], indent=2))
        else:
            print("No data found.")

if __name__ == "__main__":
    fetch_example()
