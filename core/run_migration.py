"""
Run database migration - Add trial_intervention junction table
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Get Supabase connection details
supabase_url = os.getenv("SUPABASE_URL")
project_ref = supabase_url.split('//')[1].split('.')[0]
db_password = os.getenv("SUPABASE_DB_PASSWORD")

# Build connection string
conn_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"

print("Connecting to Supabase...")
conn = psycopg2.connect(conn_string)
conn.autocommit = True
cursor = conn.cursor()

print("Running migration...")

# Read migration SQL
with open('core/migration_junction_table.sql', 'r') as f:
    migration_sql = f.read()

# Execute migration
cursor.execute(migration_sql)

print("✅ Migration complete!")

# Verify junction table was created
cursor.execute("SELECT COUNT(*) FROM trial_intervention")
count = cursor.fetchone()[0]
print(f"✅ Junction table created with {count} intervention links")

cursor.close()
conn.close()
