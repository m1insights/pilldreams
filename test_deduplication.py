"""
Test script to verify drug name deduplication logic
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from core.supabase_client import get_client
from core.drug_display_utils import get_unique_drugs, format_variant_info, should_show_variant_info

# Initialize database
db = get_client()

print("Testing Drug Name Deduplication")
print("=" * 60)

# Fetch sample drugs
print("\n1. Fetching 50 drugs from database...")
drugs_response = db.client.table('drug').select('id, name').limit(50).execute()
raw_drugs = drugs_response.data
print(f"   Raw drugs fetched: {len(raw_drugs)}")

# Show first 10 raw drug names
print("\n2. First 10 raw drug names:")
for i, drug in enumerate(raw_drugs[:10], 1):
    print(f"   {i}. {drug['name']}")

# Apply deduplication
print("\n3. Applying deduplication...")
unique_drugs = get_unique_drugs(raw_drugs)
print(f"   Unique drugs after deduplication: {len(unique_drugs)}")
print(f"   Reduction: {len(raw_drugs) - len(unique_drugs)} duplicates removed ({(1 - len(unique_drugs)/len(raw_drugs)) * 100:.1f}%)")

# Show deduplicated results
print("\n4. First 10 deduplicated drugs:")
for i, drug in enumerate(unique_drugs[:10], 1):
    display_name = drug['display_name']
    variant_count = drug['variant_count']

    variant_text = ""
    if should_show_variant_info(drug):
        variant_text = f" - {format_variant_info(variant_count)}"

    print(f"   {i}. {display_name}{variant_text}")
    if variant_count > 1:
        print(f"      Variants: {', '.join(drug['variants'][:3])}")

# Test with specific search (Metformin if exists)
print("\n5. Testing with 'metformin' search...")
search_response = db.client.table('drug').select('id, name').ilike('name', '%metformin%').limit(20).execute()
if search_response.data:
    raw_search = search_response.data
    unique_search = get_unique_drugs(raw_search)

    print(f"   Raw results: {len(raw_search)}")
    print(f"   Unique results: {len(unique_search)}")

    print("\n   Raw names:")
    for drug in raw_search[:5]:
        print(f"     - {drug['name']}")

    print("\n   Deduplicated names:")
    for drug in unique_search[:5]:
        display_name = drug['display_name']
        variant_count = drug['variant_count']
        variant_text = f" ({variant_count} variants)" if variant_count > 1 else ""
        print(f"     - {display_name}{variant_text}")
else:
    print("   No results found for 'metformin'")

print("\n" + "=" * 60)
print("Test complete!")
