"""
Neuropsych Seed Drug Loader

Loads curated neuropsych drugs and targets from the seed JSON file
into the `drugs` and `targets` tables.

Usage:
    python ingestion/seed_loader.py
    python ingestion/seed_loader.py --clear-first  # Clear existing data first
    python ingestion/seed_loader.py --targets-only  # Only load targets
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import structlog

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.supabase_client import get_client
from dotenv import load_dotenv

load_dotenv()
logger = structlog.get_logger()


def load_seed_data() -> Dict[str, Any]:
    """Load seed data from JSON file."""
    seed_path = Path(__file__).parent.parent / 'data' / 'neuropsych_seed_drugs.json'

    if not seed_path.exists():
        raise FileNotFoundError(f"Seed file not found: {seed_path}")

    with open(seed_path) as f:
        data = json.load(f)

    logger.info(
        "Loaded seed data",
        total_drugs=len(data.get('drugs', [])),
        total_targets=len(data.get('targets', []))
    )

    return data


def ensure_schema_columns(db) -> None:
    """
    Ensure required columns exist in the drugs table.

    Adds `tier` and `is_neuropsych` if they don't exist.
    Note: This requires raw SQL which Supabase may not support directly.
    These columns should be added via Supabase dashboard or migration.
    """
    # Log warning - columns should be added via Supabase dashboard
    logger.warning(
        "Schema check: Ensure 'tier' and 'is_neuropsych' columns exist in drugs table. "
        "Add via Supabase dashboard if missing: "
        "ALTER TABLE drugs ADD COLUMN IF NOT EXISTS tier VARCHAR(20) DEFAULT 'bronze'; "
        "ALTER TABLE drugs ADD COLUMN IF NOT EXISTS is_neuropsych BOOLEAN DEFAULT false;"
    )


def load_drugs(
    db,
    drugs: List[Dict[str, Any]],
    clear_first: bool = False
) -> Tuple[int, int, int]:
    """
    Load drugs into the database.

    Returns: (inserted, updated, failed)
    """
    if clear_first:
        logger.warning("Clearing existing drugs with is_neuropsych=true")
        try:
            db.client.table('drugs').delete().eq('is_neuropsych', True).execute()
        except Exception as e:
            logger.warning(f"Could not clear neuropsych drugs: {e}")

    inserted = 0
    updated = 0
    failed = 0

    for drug_data in drugs:
        try:
            # Prepare drug record
            now = datetime.now().isoformat()

            drug_record = {
                'name': drug_data['name'],
                'synonyms': drug_data.get('synonyms', []),
                'drug_class': drug_data.get('class'),
                'status': drug_data.get('status', 'approved'),
                'indications_list': drug_data.get('indications', []),
                'mechanism_summary': drug_data.get('notes'),
                'updated_at': now,
            }

            # Add tier if supported
            if drug_data.get('tier'):
                drug_record['tier'] = drug_data['tier']

            # Check if drug exists
            existing = db.client.table('drugs').select('id, name').ilike(
                'name', drug_data['name']
            ).execute()

            if existing.data:
                # Update existing
                drug_id = existing.data[0]['id']
                db.client.table('drugs').update(drug_record).eq('id', drug_id).execute()
                updated += 1
                logger.debug(f"Updated drug: {drug_data['name']}")
            else:
                # Insert new
                drug_record['created_at'] = now
                result = db.client.table('drugs').insert(drug_record).execute()
                if result.data:
                    inserted += 1
                    logger.debug(f"Inserted drug: {drug_data['name']}")
                else:
                    failed += 1

        except Exception as e:
            failed += 1
            logger.error(f"Failed to load drug {drug_data.get('name')}: {e}")

    return inserted, updated, failed


def load_targets(
    db,
    targets: List[Dict[str, Any]],
    clear_first: bool = False
) -> Tuple[int, int, int]:
    """
    Load targets into the database.

    Returns: (inserted, updated, failed)
    """
    if clear_first:
        logger.warning("Clearing existing targets")
        # Don't clear all targets - only add/update

    inserted = 0
    updated = 0
    failed = 0

    for target_data in targets:
        try:
            # Prepare target record
            now = datetime.now().isoformat()

            target_record = {
                'symbol': target_data['symbol'],
                'uniprot_id': target_data.get('uniprot_id'),
                'description': target_data.get('name'),
                'pathway': target_data.get('pathway'),
            }

            # Check if target exists by symbol
            existing = db.client.table('targets').select('id, symbol').eq(
                'symbol', target_data['symbol']
            ).execute()

            if existing.data:
                # Update existing
                target_id = existing.data[0]['id']
                db.client.table('targets').update(target_record).eq('id', target_id).execute()
                updated += 1
                logger.debug(f"Updated target: {target_data['symbol']}")
            else:
                # Insert new
                target_record['created_at'] = now
                result = db.client.table('targets').insert(target_record).execute()
                if result.data:
                    inserted += 1
                    logger.debug(f"Inserted target: {target_data['symbol']}")
                else:
                    failed += 1

        except Exception as e:
            failed += 1
            logger.error(f"Failed to load target {target_data.get('symbol')}: {e}")

    return inserted, updated, failed


def verify_data(db) -> Dict[str, int]:
    """Verify loaded data."""
    stats = {}

    # Count drugs
    drugs = db.client.table('drugs').select('id', count='exact').execute()
    stats['total_drugs'] = drugs.count

    # Count by tier (if column exists)
    try:
        gold = db.client.table('drugs').select('id', count='exact').eq('tier', 'gold').execute()
        stats['gold_tier'] = gold.count
        silver = db.client.table('drugs').select('id', count='exact').eq('tier', 'silver').execute()
        stats['silver_tier'] = silver.count
        bronze = db.client.table('drugs').select('id', count='exact').eq('tier', 'bronze').execute()
        stats['bronze_tier'] = bronze.count
    except:
        pass

    # Count targets
    targets = db.client.table('targets').select('id', count='exact').execute()
    stats['total_targets'] = targets.count

    # Count drug-target links
    links = db.client.table('drug_targets').select('id', count='exact').execute()
    stats['drug_target_links'] = links.count

    return stats


def main():
    parser = argparse.ArgumentParser(description="Load neuropsych seed drugs and targets")
    parser.add_argument('--clear-first', action='store_true', help="Clear existing neuropsych data first")
    parser.add_argument('--targets-only', action='store_true', help="Only load targets")
    parser.add_argument('--drugs-only', action='store_true', help="Only load drugs")
    parser.add_argument('--verify', action='store_true', help="Only verify existing data")

    args = parser.parse_args()

    # Initialize database connection
    db = get_client()

    # Ensure schema columns
    ensure_schema_columns(db)

    if args.verify:
        stats = verify_data(db)
        print("\n=== Database Stats ===")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        return

    # Load seed data
    seed_data = load_seed_data()

    results = {}

    # Load targets
    if not args.drugs_only:
        targets = seed_data.get('targets', [])
        logger.info(f"Loading {len(targets)} targets...")
        inserted, updated, failed = load_targets(db, targets, args.clear_first)
        results['targets'] = {'inserted': inserted, 'updated': updated, 'failed': failed}
        print(f"Targets: {inserted} inserted, {updated} updated, {failed} failed")

    # Load drugs
    if not args.targets_only:
        drugs = seed_data.get('drugs', [])
        logger.info(f"Loading {len(drugs)} drugs...")
        inserted, updated, failed = load_drugs(db, drugs, args.clear_first)
        results['drugs'] = {'inserted': inserted, 'updated': updated, 'failed': failed}
        print(f"Drugs: {inserted} inserted, {updated} updated, {failed} failed")

    # Verify
    print("\n=== Verification ===")
    stats = verify_data(db)
    for key, value in stats.items():
        print(f"  {key}: {value}")

    return results


if __name__ == "__main__":
    main()
