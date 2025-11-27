import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.etl import supabase_client

def clear_pipeline():
    load_dotenv()
    if not supabase_client.supabase:
        print("Supabase client not initialized.")
        return

    try:
        # Delete all rows from pipeline_assets
        # Note: Cascade delete should handle related tables if configured, 
        # but let's be safe and rely on the schema's ON DELETE CASCADE
        supabase_client.supabase.table("pipeline_assets").delete().neq("id", 0).execute()
        print("✅ Cleared pipeline_assets table.")
    except Exception as e:
        print(f"❌ Error clearing pipeline assets: {e}")

if __name__ == "__main__":
    clear_pipeline()
