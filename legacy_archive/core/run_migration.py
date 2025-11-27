"""
Run Database Migration

Applies SQL migration files to the Supabase database.

Usage:
    python core/run_migration.py schema_company.sql
    python core/run_migration.py migration_junction_table.sql
"""

import os
import sys
from pathlib import Path
import psycopg2
from dotenv import load_dotenv
import structlog

load_dotenv()
logger = structlog.get_logger()


def run_migration(migration_file: str):
    """
    Apply a SQL migration file to the database.

    Args:
        migration_file: Path to .sql file
    """
    # Load SQL
    sql_path = Path(migration_file)
    if not sql_path.exists():
        # Try relative to core directory
        sql_path = Path(__file__).parent / migration_file
        if not sql_path.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return False

    with open(sql_path) as f:
        migration_sql = f.read()

    # Build connection string
    supabase_url = os.getenv("SUPABASE_URL")
    db_password = os.getenv("SUPABASE_DB_PASSWORD")

    if not supabase_url or not db_password:
        logger.error("SUPABASE_URL and SUPABASE_DB_PASSWORD must be set in .env")
        return False

    # Parse project ref from URL (e.g., https://xxxxx.supabase.co)
    project_ref = supabase_url.split('//')[1].split('.')[0]

    conn_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"

    logger.info(f"Connecting to database...", project_ref=project_ref)

    try:
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        cursor = conn.cursor()

        logger.info(f"Running migration: {sql_path.name}")
        cursor.execute(migration_sql)

        cursor.close()
        conn.close()

        logger.info(f"Migration completed successfully: {sql_path.name}")
        return True

    except Exception as e:
        logger.error(f"Migration failed", error=str(e))
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python core/run_migration.py <migration_file.sql>")
        print("\nAvailable migrations:")
        migrations_dir = Path(__file__).parent
        for f in sorted(migrations_dir.glob("*.sql")):
            print(f"  - {f.name}")
        sys.exit(1)

    migration_file = sys.argv[1]
    success = run_migration(migration_file)
    sys.exit(0 if success else 1)
