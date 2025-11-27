import os
import psycopg2
from dotenv import load_dotenv

def apply_schema():
    load_dotenv()
    db_url = os.getenv("SUPABASE_DB_URL")
    if not db_url:
        # Try to construct from URL and Key? No, need direct connection string.
        # Often SUPABASE_DB_URL is provided in .env
        print("❌ SUPABASE_DB_URL not found in .env")
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
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Schema applied successfully.")
    except Exception as e:
        print(f"❌ Error applying schema: {e}")

if __name__ == "__main__":
    apply_schema()
