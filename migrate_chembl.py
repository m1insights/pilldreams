import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.etl import supabase_client

def migrate_chembl():
    load_dotenv()
    if not supabase_client.supabase:
        print("Supabase client not initialized.")
        return

    sql = """
    -- ChEMBL Metrics (Chemistry Quality Layer)
    CREATE TABLE IF NOT EXISTS chembl_metrics (
      id SERIAL PRIMARY KEY,
      drug_id INT REFERENCES drugs(id) ON DELETE CASCADE,
      pipeline_asset_id INT REFERENCES pipeline_assets(id) ON DELETE CASCADE,
      p_act_median FLOAT,
      p_act_best FLOAT,
      p_off_best FLOAT,
      delta_p FLOAT,
      n_activities_primary INT,
      n_activities_total INT,
      chem_score FLOAT,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_chembl_metrics_drug ON chembl_metrics(drug_id);
    CREATE INDEX IF NOT EXISTS idx_chembl_metrics_pipeline ON chembl_metrics(pipeline_asset_id);
    """

    try:
        # Supabase-py doesn't support raw SQL execution directly on the client object usually, 
        # but we can use the `rpc` call if we had a function, or just use `psycopg2` if we had connection string.
        # However, for this environment, we might need to rely on the user running it or use a workaround.
        # Wait, previous migrations were done by "applying new schema". 
        # Let's try to use the `rpc` if available or just print instructions?
        # Actually, I can use the `postgres` library if I have the connection string.
        # But I don't have the connection string in the env, only URL and Key.
        # Let's check if `supabase_client` has a way.
        # If not, I will assume I can't run DDL via the client easily without a stored procedure.
        # BUT, I previously ran `cleanup_project.py` which didn't do DDL.
        # I previously ran `verify_setup.py`.
        # I previously modified `core/schema_pivot.sql`.
        # The user might need to run this SQL manually or I can try to use `psycopg2` if I can derive the connection string.
        # Let's look at `.env` to see if I can get the DB connection string.
        pass
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # For now, I will just print the SQL and ask the user to run it? 
    # No, I should try to execute it.
    # Actually, I can use the `postgres` connection if I can find the credentials.
    # Let's check `.env` first.
    pass
