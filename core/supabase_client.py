"""
Supabase Client - Database connection and initialization

Handles Supabase connection, schema initialization, and seeding.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
from dotenv import load_dotenv
import structlog

logger = structlog.get_logger()

# Load environment variables
load_dotenv()


class SupabaseClient:
    """Supabase database client wrapper"""

    def __init__(self):
        """Initialize Supabase client"""
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")

        if not self.url or not self.key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in .env file"
            )

        self.client: Client = create_client(self.url, self.key)
        logger.info("Supabase client initialized", url=self.url)

    def execute_sql(self, sql: str) -> Dict[str, Any]:
        """
        Execute raw SQL query.

        Args:
            sql: SQL query string

        Returns:
            Query result
        """
        try:
            result = self.client.rpc("execute_sql", {"query": sql}).execute()
            logger.info("SQL executed successfully")
            return result.data
        except Exception as e:
            logger.error("SQL execution failed", error=str(e))
            raise

    def init_schema(self):
        """
        Initialize database schema.

        Creates all tables from schema.sql file.
        """
        schema_file = Path(__file__).parent / "schema.sql"

        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")

        with open(schema_file) as f:
            schema_sql = f.read()

        logger.info("Initializing database schema...")

        # Execute the full schema SQL via Supabase SQL endpoint
        # Note: This requires database password and direct connection
        try:
            # For now, we'll execute via psycopg2 connection
            import psycopg2

            # Parse the project ref from URL
            project_ref = self.url.split('//')[1].split('.')[0]

            # Build connection string
            conn_string = f"postgresql://postgres:{os.getenv('SUPABASE_DB_PASSWORD')}@db.{project_ref}.supabase.co:5432/postgres"

            conn = psycopg2.connect(conn_string)
            conn.autocommit = True
            cursor = conn.cursor()

            # Execute the full schema
            cursor.execute(schema_sql)

            cursor.close()
            conn.close()

            logger.info("Database schema initialized successfully")

        except ImportError:
            logger.warning("psycopg2 not installed, trying alternative method...")
            # Fallback: execute statements one by one via Supabase REST API
            # This is less reliable but doesn't require psycopg2
            statements = [s.strip() for s in schema_sql.split(';') if s.strip()]

            for i, stmt in enumerate(statements):
                logger.info(f"Executing statement {i+1}/{len(statements)}")
                # This would need a custom RPC function in Supabase
                logger.warning(f"Cannot execute via REST API: {stmt[:100]}...")

            logger.warning("Schema initialization incomplete - please run SQL manually in Supabase SQL Editor")

        except Exception as e:
            logger.error(f"Failed to initialize schema", error=str(e))
            raise

    def seed_data(self):
        """
        Seed database with sample data.

        Inserts placeholder drugs for testing.
        """
        logger.info("Seeding database with sample data...")

        # Sample drugs
        sample_drugs = [
            {
                "name": "Metformin",
                "synonyms": ["Glucophage", "Fortamet"],
                "class": "Antidiabetic",
                "is_approved": True,
                "drugbank_id": "DB00331",
                "chembl_id": "CHEMBL1431"
            },
            {
                "name": "Aspirin",
                "synonyms": ["Acetylsalicylic acid", "ASA"],
                "class": "Analgesic",
                "is_approved": True,
                "drugbank_id": "DB00945",
                "chembl_id": "CHEMBL25"
            },
            {
                "name": "Sertraline",
                "synonyms": ["Zoloft"],
                "class": "Antidepressant",
                "is_approved": True,
                "drugbank_id": "DB01104",
                "chembl_id": "CHEMBL809"
            }
        ]

        try:
            result = self.client.table("Drug").insert(sample_drugs).execute()
            logger.info(f"Inserted {len(sample_drugs)} sample drugs")
        except Exception as e:
            logger.error("Failed to seed data", error=str(e))
            raise

        logger.info("Database seeding completed")


# Singleton instance
_supabase_client: Optional[SupabaseClient] = None


def get_client() -> SupabaseClient:
    """Get or create Supabase client singleton"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Supabase database management")
    parser.add_argument("--init", action="store_true", help="Initialize schema")
    parser.add_argument("--seed", action="store_true", help="Seed sample data")

    args = parser.parse_args()

    client = get_client()

    if args.init:
        client.init_schema()

    if args.seed:
        client.seed_data()

    if not (args.init or args.seed):
        print("Use --init to initialize schema or --seed to add sample data")
