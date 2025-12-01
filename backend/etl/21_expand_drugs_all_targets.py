"""
ETL Script: 21_expand_drugs_all_targets.py
Controlled expansion of drugs around existing 79 epigenetic targets.

This script:
1. Gets all targets that have fewer than N drugs linked
2. Queries Open Targets for known drugs for each target
3. Adds new drugs (with ChEMBL IDs) and creates drug-target links
4. Filters to only include drugs with relevant oncology indications

Usage:
    python -m backend.etl.21_expand_drugs_all_targets
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from backend.etl.supabase_client import supabase
from backend.etl import open_targets

# Minimum drugs per target before we consider it "covered"
MIN_DRUGS_PER_TARGET = 2

# Skip these targets (non-epigenetic or special cases)
SKIP_TARGETS = set()

# Oncology EFO IDs to filter on (only add drugs with oncology relevance)
ONCOLOGY_EFO_PREFIXES = [
    'EFO_0000311',   # cancer
    'EFO_0000616',   # neoplasm
    'MONDO_0004992', # cancer
    'MONDO_0005070', # neoplasm
]


def get_targets_needing_drugs():
    """Find targets with fewer than MIN_DRUGS_PER_TARGET drugs."""
    print(f"\n🔍 Finding targets with < {MIN_DRUGS_PER_TARGET} drugs...")

    # Get all targets
    targets = supabase.table('epi_targets').select('id, symbol, ot_target_id').execute().data

    # Get drug-target links
    links = supabase.table('epi_drug_targets').select('target_id').execute().data
    target_drug_counts = {}
    for link in links:
        tid = link['target_id']
        target_drug_counts[tid] = target_drug_counts.get(tid, 0) + 1

    # Filter to targets needing more drugs
    needing_drugs = []
    for target in targets:
        count = target_drug_counts.get(target['id'], 0)
        symbol = target['symbol']

        if symbol in SKIP_TARGETS:
            continue

        if count < MIN_DRUGS_PER_TARGET:
            needing_drugs.append({
                **target,
                'current_drug_count': count
            })

    print(f"  Found {len(needing_drugs)} targets needing drug expansion")
    return needing_drugs


def populate_missing_ot_ids(targets):
    """Look up OT target IDs for targets that don't have one."""
    print("\n🔍 Checking for missing OT target IDs...")

    missing = [t for t in targets if not t.get('ot_target_id')]
    if not missing:
        print("  ✓ All targets have OT IDs")
        return

    print(f"  {len(missing)} targets need OT ID lookup")

    updated = 0
    for target in missing:
        symbol = target['symbol']
        print(f"  Looking up {symbol}...", end=" ")

        try:
            ot_result = open_targets.search_target_by_symbol(symbol)
            if ot_result:
                ot_id = ot_result['id']
                supabase.table('epi_targets').update({
                    'ot_target_id': ot_id
                }).eq('id', target['id']).execute()
                target['ot_target_id'] = ot_id  # Update local copy too
                print(f"✓ {ot_id}")
                updated += 1
            else:
                print("✗ Not found in Open Targets")
        except Exception as e:
            print(f"✗ Error: {e}")

    print(f"  Updated {updated}/{len(missing)} targets")


def is_oncology_relevant(diseases):
    """Check if any disease is oncology-related."""
    if not diseases:
        return True  # If no disease info, include it (might be preclinical)

    for disease in diseases:
        if not disease:
            continue
        efo_id = disease.get('id', '')
        # Check if starts with any oncology prefix
        for prefix in ONCOLOGY_EFO_PREFIXES:
            if efo_id.startswith(prefix.split('_')[0]):  # Match EFO or MONDO prefix
                return True
        # Also check name for cancer-related terms
        name = disease.get('name', '').lower()
        oncology_terms = ['cancer', 'carcinoma', 'lymphoma', 'leukemia', 'myeloma',
                         'tumor', 'tumour', 'neoplasm', 'melanoma', 'sarcoma',
                         'glioma', 'glioblastoma', 'blastoma']
        if any(term in name for term in oncology_terms):
            return True

    return False


def fetch_drugs_for_all_targets(targets):
    """Fetch drugs from Open Targets for all targets needing expansion."""
    print("\n💊 Fetching drugs for targets...")

    # Get existing drugs to avoid duplicates
    existing_drugs = supabase.table('epi_drugs').select('id, chembl_id, name').execute().data
    existing_chembl_ids = {d['chembl_id']: d['id'] for d in existing_drugs if d['chembl_id']}
    existing_names = {d['name'].upper(): d['id'] for d in existing_drugs}

    # Get existing drug-target links
    existing_links = supabase.table('epi_drug_targets').select('drug_id, target_id').execute().data
    existing_link_set = {(l['drug_id'], l['target_id']) for l in existing_links}

    drugs_added = 0
    links_added = 0
    skipped_non_oncology = 0

    for i, target in enumerate(targets):
        symbol = target['symbol']
        ot_id = target.get('ot_target_id')

        if not ot_id:
            print(f"\n  [{i+1}/{len(targets)}] ⚠️ {symbol} - no OT ID, skipping")
            continue

        print(f"\n  [{i+1}/{len(targets)}] {symbol} (currently {target['current_drug_count']} drugs)")

        try:
            drugs = open_targets.fetch_known_drugs_for_target(ot_id)

            if not drugs:
                print(f"    No drugs found in Open Targets")
                continue

            # Group by drug to dedupe
            unique_drugs = {}
            for entry in drugs:
                drug_info = entry['drug']
                drug_id = drug_info['id']  # ChEMBL ID

                if drug_id not in unique_drugs:
                    unique_drugs[drug_id] = {
                        'chembl_id': drug_id,
                        'name': drug_info['name'],
                        'max_phase': drug_info.get('maximumClinicalTrialPhase', 0),
                        'drug_type': drug_info.get('drugType', 'Small molecule'),
                        'mechanisms': set(),
                        'diseases': []
                    }

                moa = entry.get('mechanismOfAction', '')
                if moa:
                    unique_drugs[drug_id]['mechanisms'].add(moa)

                if entry.get('disease'):
                    unique_drugs[drug_id]['diseases'].append(entry['disease'])

            print(f"    Found {len(unique_drugs)} unique drugs")

            added_for_target = 0
            for chembl_id, drug_data in unique_drugs.items():
                drug_name = drug_data['name']

                # Check oncology relevance
                if not is_oncology_relevant(drug_data['diseases']):
                    skipped_non_oncology += 1
                    continue

                # Check if drug already exists
                existing_drug_id = existing_chembl_ids.get(chembl_id) or existing_names.get(drug_name.upper())

                if existing_drug_id:
                    # Drug exists - just check if link exists
                    if (existing_drug_id, target['id']) not in existing_link_set:
                        mechanism = list(drug_data['mechanisms'])[0] if drug_data['mechanisms'] else None
                        supabase.table('epi_drug_targets').insert({
                            'drug_id': existing_drug_id,
                            'target_id': target['id'],
                            'mechanism_of_action': mechanism,
                            'is_primary_target': True
                        }).execute()
                        links_added += 1
                        existing_link_set.add((existing_drug_id, target['id']))
                        print(f"    → Linked existing {drug_name}")
                else:
                    # Insert new drug
                    mechanism = list(drug_data['mechanisms'])[0] if drug_data['mechanisms'] else None
                    phase = drug_data['max_phase']
                    is_approved = phase == 4

                    new_drug = {
                        'name': drug_name,
                        'chembl_id': chembl_id,
                        'drug_type': drug_data['drug_type'],
                        'fda_approved': is_approved,
                        'source': 'OpenTargets',
                        'modality': 'small_molecule' if 'small' in drug_data['drug_type'].lower() else 'biologic'
                    }

                    result = supabase.table('epi_drugs').insert(new_drug).execute()
                    new_drug_id = result.data[0]['id']
                    drugs_added += 1
                    added_for_target += 1
                    existing_chembl_ids[chembl_id] = new_drug_id
                    existing_names[drug_name.upper()] = new_drug_id

                    # Create drug-target link
                    supabase.table('epi_drug_targets').insert({
                        'drug_id': new_drug_id,
                        'target_id': target['id'],
                        'mechanism_of_action': mechanism,
                        'is_primary_target': True
                    }).execute()
                    links_added += 1
                    existing_link_set.add((new_drug_id, target['id']))

                    phase_str = f"Phase {phase}" if phase else "Preclinical"
                    print(f"    + {drug_name} ({phase_str})")

            if added_for_target > 0:
                print(f"    Added {added_for_target} new drugs for {symbol}")

        except Exception as e:
            print(f"    ✗ Error: {e}")
            import traceback
            traceback.print_exc()

    return drugs_added, links_added, skipped_non_oncology


def print_summary():
    """Print summary of drugs per target."""
    print("\n📋 Drugs per target (top 30):")

    result = supabase.table('epi_drug_targets').select('target_id, epi_targets(symbol)').execute()
    target_counts = {}
    for link in result.data:
        symbol = link.get('epi_targets', {}).get('symbol', 'Unknown')
        target_counts[symbol] = target_counts.get(symbol, 0) + 1

    for symbol, count in sorted(target_counts.items(), key=lambda x: -x[1])[:30]:
        print(f"  {symbol}: {count}")

    # Targets with no drugs
    all_targets = supabase.table('epi_targets').select('symbol').execute().data
    all_symbols = {t['symbol'] for t in all_targets}
    no_drugs = all_symbols - set(target_counts.keys())

    if no_drugs:
        print(f"\n⚠️ Targets with NO drugs ({len(no_drugs)}):")
        for symbol in sorted(no_drugs)[:20]:
            print(f"  {symbol}")
        if len(no_drugs) > 20:
            print(f"  ... and {len(no_drugs) - 20} more")


def run():
    print("=" * 60)
    print("ETL: Expand Drugs for All Epigenetic Targets")
    print("=" * 60)

    if not supabase:
        print("❌ Supabase client not initialized.")
        return

    # Step 1: Find targets needing drugs
    targets = get_targets_needing_drugs()

    if not targets:
        print("\n✅ All targets have sufficient drug coverage!")
        print_summary()
        return

    # Step 2: Populate missing OT IDs
    populate_missing_ot_ids(targets)

    # Step 3: Fetch drugs for all targets
    drugs_added, links_added, skipped = fetch_drugs_for_all_targets(targets)

    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print(f"  New drugs added: {drugs_added}")
    print(f"  New drug-target links: {links_added}")
    print(f"  Skipped (non-oncology): {skipped}")

    print_summary()

    print("\n✅ Drug expansion complete!")


if __name__ == "__main__":
    run()
