import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.etl import supabase_client

def check_counts():
    load_dotenv()
    if not supabase_client.supabase:
        print("Supabase client not initialized.")
        return

    tables = ["drugs", "drug_indications", "drug_targets"]
    print("Database Counts:")
    for table in tables:
        try:
            response = supabase_client.supabase.table(table).select("count", count="exact").execute()
            print(f"- {table}: {response.count}")
        except Exception as e:
            print(f"- {table}: Error ({e})")

    # Check for enrichment (drugs with pubmed_count > 0)
    try:
        response = supabase_client.supabase.table("drugs").select("count", count="exact").gt("pubmed_count", 0).execute()
        print(f"- Enriched drugs (PubMed > 0): {response.count}")
    except Exception as e:
        print(f"- Enriched drugs: Error ({e})")

if __name__ == "__main__":
    check_counts()
