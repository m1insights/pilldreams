"""
ETL Script: Ingest epigenetic patents from CSV.
Links patents to targets and drugs where possible.
"""
import sys
import os
import csv
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from backend.etl.supabase_client import supabase

CSV_PATH = os.path.join(os.path.dirname(__file__), "seed_epi_patents.csv")


def resolve_target_symbols(symbols_str: str) -> list:
    """Parse semicolon-separated target symbols and verify they exist."""
    if not symbols_str:
        return []

    symbols = [s.strip() for s in symbols_str.split(';') if s.strip()]
    valid_symbols = []

    for symbol in symbols:
        result = supabase.table('epi_targets').select('symbol').eq('symbol', symbol).execute()
        if result.data:
            valid_symbols.append(symbol)
        else:
            print(f"    ⚠️ Target not found: {symbol}")

    return valid_symbols


def run():
    print("📜 Ingesting epigenetic patents...")

    if not supabase:
        print("❌ Supabase client not initialized.")
        return

    if not os.path.exists(CSV_PATH):
        print(f"❌ CSV file not found: {CSV_PATH}")
        return

    with open(CSV_PATH, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"📄 Found {len(rows)} patents in CSV")

    inserted = 0
    updated = 0

    for row in rows:
        patent_number = row['patent_number']
        print(f"\n📜 Processing: {patent_number}")

        # Check if exists
        existing = supabase.table('epi_patents').select('id').eq('patent_number', patent_number).execute()

        # Resolve target symbols
        related_targets = resolve_target_symbols(row.get('related_target_symbols', ''))
        if related_targets:
            print(f"    Targets: {related_targets}")

        # Parse date
        pub_date = row.get('pub_date')
        if pub_date and len(pub_date) == 10:
            pass  # Valid date format
        else:
            pub_date = None

        patent_data = {
            'patent_number': patent_number,
            'title': row['title'],
            'assignee': row.get('assignee') or None,
            'first_inventor': row.get('first_inventor') or None,
            'pub_date': pub_date,
            'category': row.get('category') or None,
            'abstract_snippet': row.get('abstract_snippet') or None,
            'related_target_symbols': related_targets if related_targets else None,
        }

        if existing.data:
            supabase.table('epi_patents').update(patent_data).eq('id', existing.data[0]['id']).execute()
            print(f"  ✅ Updated {patent_number}")
            updated += 1
        else:
            supabase.table('epi_patents').insert(patent_data).execute()
            print(f"  ✅ Inserted {patent_number}")
            inserted += 1

    # Summary
    print(f"\n📊 Summary:")
    print(f"  Inserted: {inserted}")
    print(f"  Updated: {updated}")

    # Category breakdown
    patents = supabase.table('epi_patents').select('category').execute().data
    categories = {}
    for p in patents:
        cat = p.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1

    print(f"\n📋 Patents by category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    print("\n✅ Patent ingestion complete!")


if __name__ == "__main__":
    run()
