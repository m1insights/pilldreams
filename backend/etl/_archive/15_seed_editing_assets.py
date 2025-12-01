"""
ETL Script: Seed epigenetic editing assets from CSV.
Resolves target_id and indication_id, inserts missing targets/indications as needed.
"""
import sys
import os
import csv
import json
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from backend.etl.supabase_client import supabase

CSV_PATH = os.path.join(os.path.dirname(__file__), "seed_epi_editors.csv")

# Indication name -> EFO ID mapping (for indications we might need to create)
INDICATION_EFO_MAP = {
    'Hypercholesterolemia': 'EFO_0003891',
    'Hepatocellular carcinoma': 'EFO_0000182',
    'HCC': 'EFO_0000182',
    'Hepatitis B': 'EFO_0004197',
    'FSHD': 'Orphanet_269',  # Facioscapulohumeral dystrophy
    'ATTR Amyloidosis': 'Orphanet_85447',
    'Cancer': 'MONDO_0004992',
}


def get_or_create_target(symbol: str) -> str:
    """Get target ID by symbol, or create if missing."""
    result = supabase.table('epi_targets').select('id').eq('symbol', symbol).execute()
    if result.data:
        return result.data[0]['id']

    # Create new target
    print(f"    Creating new target: {symbol}")
    new_target = {
        'symbol': symbol,
        'family': 'other',
        'class': 'other',
        'is_core_epigenetic': False,
    }
    result = supabase.table('epi_targets').insert(new_target).execute()
    return result.data[0]['id']


def get_or_create_indication(name: str) -> str:
    """Get indication ID by name, or create if missing."""
    # Try exact match first
    result = supabase.table('epi_indications').select('id').ilike('name', name).execute()
    if result.data:
        return result.data[0]['id']

    # Try partial match
    result = supabase.table('epi_indications').select('id, name').execute()
    for ind in result.data:
        if name.lower() in ind['name'].lower() or ind['name'].lower() in name.lower():
            return ind['id']

    # Create new indication
    print(f"    Creating new indication: {name}")
    efo_id = INDICATION_EFO_MAP.get(name)
    new_indication = {
        'name': name,
        'efo_id': efo_id,
        'disease_area': 'Oncology' if 'cancer' in name.lower() or 'carcinoma' in name.lower() else 'Other',
    }
    result = supabase.table('epi_indications').insert(new_indication).execute()
    return result.data[0]['id']


def run():
    print("🧬 Seeding epigenetic editing assets...")

    if not supabase:
        print("❌ Supabase client not initialized.")
        return

    if not os.path.exists(CSV_PATH):
        print(f"❌ CSV file not found: {CSV_PATH}")
        return

    with open(CSV_PATH, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"📄 Found {len(rows)} editing assets in CSV")

    inserted = 0
    updated = 0

    for row in rows:
        name = row['name']
        print(f"\n📦 Processing: {name}")

        # Check if exists
        existing = supabase.table('epi_editing_assets').select('id').eq('name', name).execute()

        # Resolve target
        target_id = None
        if row.get('target_gene_symbol'):
            target_id = get_or_create_target(row['target_gene_symbol'])
            print(f"    Target: {row['target_gene_symbol']} -> {target_id}")

        # Resolve indication
        indication_id = None
        if row.get('primary_indication'):
            indication_id = get_or_create_indication(row['primary_indication'])
            print(f"    Indication: {row['primary_indication']} -> {indication_id}")

        # Parse effector domains (JSON array)
        effector_domains = None
        if row.get('effector_domains'):
            try:
                effector_domains = json.loads(row['effector_domains'])
            except json.JSONDecodeError:
                effector_domains = row['effector_domains'].split(',')

        # Parse phase
        phase = None
        if row.get('phase') and row['phase'].strip():
            try:
                phase = int(row['phase'])
            except ValueError:
                pass

        asset_data = {
            'name': name,
            'sponsor': row.get('sponsor') or None,
            'modality': 'epigenetic_editor',
            'delivery_type': row.get('delivery_type') or None,
            'dbd_type': row.get('dbd_type') or None,
            'effector_type': row.get('effector_type') or None,
            'effector_domains': effector_domains,
            'target_gene_symbol': row.get('target_gene_symbol') or None,
            'target_gene_id': target_id,  # Note: column name in existing table
            'indication_id': indication_id,  # Note: column name in existing table
            'phase': phase,
            'status': row.get('status') or 'preclinical',
            'description': row.get('description') or None,
            'source_url': row.get('source_url') or None,
        }

        if existing.data:
            # Update
            supabase.table('epi_editing_assets').update(asset_data).eq('id', existing.data[0]['id']).execute()
            print(f"  ✅ Updated {name}")
            updated += 1
        else:
            # Insert
            supabase.table('epi_editing_assets').insert(asset_data).execute()
            print(f"  ✅ Inserted {name}")
            inserted += 1

    print(f"\n📊 Summary:")
    print(f"  Inserted: {inserted}")
    print(f"  Updated: {updated}")
    print(f"  Total: {inserted + updated}")

    # Show all editing assets
    assets = supabase.table('epi_editing_assets').select('name, sponsor, dbd_type, status').execute().data
    print(f"\n📋 All editing assets ({len(assets)}):")
    for a in assets:
        print(f"  - {a['name']} ({a.get('sponsor', 'Unknown')}) [{a.get('dbd_type', '?')}] - {a.get('status', '?')}")

    print("\n✅ Editing asset seeding complete!")


if __name__ == "__main__":
    run()
