import os
import sys
from dotenv import load_dotenv
import requests

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.etl import supabase_client, open_targets

def verify_environment():
    print("Verifying Environment...")
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url:
        print("❌ SUPABASE_URL is missing in .env")
    else:
        print("✅ SUPABASE_URL found")
        
    if not key:
        print("❌ SUPABASE_SERVICE_KEY is missing in .env")
    else:
        print("✅ SUPABASE_SERVICE_KEY found")
        
    return bool(url and key)

def verify_open_targets():
    print("\nVerifying Open Targets Connectivity...")
    try:
        # Fetch just one drug to test
        efo_id = "MONDO_0002009" # MDD
        print(f"Querying for {efo_id}...")
        # We'll just run the query function directly with a small limit if possible, 
        # but our function fetches all. Let's just call it and break early or modify the function?
        # The function `fetch_known_drugs_for_disease` fetches ALL. That might be slow for a quick check.
        # Let's just run a raw query here to be safe and quick.
        
        query = """
        query KnownDrugs($efoId: String!) {
          disease(efoId: $efoId) {
            id
            name
          }
        }
        """
        result = open_targets.run_ot_query(query, {"efoId": efo_id})
        name = result["data"]["disease"]["name"]
        print(f"✅ Successfully connected to Open Targets. Disease: {name}")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Open Targets: {e}")
        return False

def verify_supabase_connection():
    print("\nVerifying Supabase Connection...")
    if not supabase_client.supabase:
        print("❌ Supabase client not initialized.")
        return False
        
    try:
        # Try to select from drugs table (should be empty but exist)
        response = supabase_client.supabase.table("drugs").select("count", count="exact").execute()
        print(f"✅ Successfully connected to Supabase. Drugs table count: {response.count}")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return False

if __name__ == "__main__":
    env_ok = verify_environment()
    ot_ok = verify_open_targets()
    sb_ok = verify_supabase_connection()
    
    if env_ok and ot_ok and sb_ok:
        print("\n🎉 All systems go! You can now run the backend and frontend.")
    else:
        print("\n⚠️ Some checks failed. Please fix the issues above.")
