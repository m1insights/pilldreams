import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    # Try to construct from other vars if possible, or just fail
    print("DATABASE_URL not found in .env. Please run the SQL manually or set DATABASE_URL.")
    exit(1)

try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    # Drop existing tables if we want to start fresh (User said "wipe clean")
    # Be careful, but user said "wipe supabase clean".
    # I'll add DROP TABLE IF EXISTS to the SQL execution or just rely on the script.
    # The schema file has CREATE TABLE. I should probably add DROP TABLE to the schema or here.
    # Let's just run the schema file. If it fails due to existing tables, I might need to drop them.
    # I'll prepend drops here.
    
    drops = """
    DROP TABLE IF EXISTS drug_id_map CASCADE;
    DROP TABLE IF EXISTS drug_targets CASCADE;
    DROP TABLE IF EXISTS drug_indications CASCADE;
    DROP TABLE IF EXISTS drugs CASCADE;
    """
    cur.execute(drops)
    
    with open("../core/schema_pivot.sql", "r") as f:
        sql = f.read()
        
    cur.execute(sql)
    conn.commit()
    print("Migration successful.")
    
except Exception as e:
    print(f"Migration failed: {e}")
    exit(1)
