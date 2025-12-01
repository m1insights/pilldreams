"""
ETL Script: Pull drugs from Open Targets for new epigenetic targets.

This script:
1. Finds targets missing ot_target_id and looks them up
2. Fetches known drugs for all new targets (NSD2, EP300, KAT2A, etc.)
3. Inserts new drugs and creates drug-target links
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from backend.etl.supabase_client import supabase
from backend.etl import open_targets

# Targets we specifically want to pull drugs for
PRIORITY_TARGETS = ['NSD2', 'EP300', 'KAT2A', 'METTL7A', 'YTHDF1', 'H2AFY', 'ASXL1', 'PCSK9', 'MYC', 'DUX4']


def populate_missing_ot_ids():
    """Find targets with NULL ot_target_id and look them up."""
    print("\n🔍 Looking up missing OT target IDs...")

    result = supabase.table('epi_targets').select('id, symbol, ot_target_id').is_('ot_target_id', 'null').execute()
    targets_missing = result.data

    if not targets_missing:
        print("  ✓ All targets have OT IDs")
        return

    print(f"  Found {len(targets_missing)} targets without OT IDs")

    updated = 0
    for target in targets_missing:
        symbol = target['symbol']
        print(f"  Searching for {symbol}...", end=" ")

        try:
            ot_result = open_targets.search_target_by_symbol(symbol)
            if ot_result:
                ot_id = ot_result['id']
                supabase.table('epi_targets').update({
                    'ot_target_id': ot_id
                }).eq('id', target['id']).execute()
                print(f"✓ {ot_id}")
                updated += 1
            else:
                print("✗ Not found in Open Targets")
        except Exception as e:
            print(f"✗ Error: {e}")

    print(f"\n  Updated {updated}/{len(targets_missing)} targets")


def fetch_drugs_for_targets():
    """Fetch drugs from Open Targets for priority targets."""
    print("\n💊 Fetching drugs for priority targets...")

    # Get priority targets with their OT IDs
    result = supabase.table('epi_targets').select('id, symbol, ot_target_id').execute()
    all_targets = {t['symbol']: t for t in result.data}

    # Get existing drugs to avoid duplicates
    existing_drugs = supabase.table('epi_drugs').select('chembl_id, name').execute().data
    existing_chembl_ids = {d['chembl_id'] for d in existing_drugs if d['chembl_id']}
    existing_names = {d['name'].upper() for d in existing_drugs}

    print(f"  Existing drugs: {len(existing_chembl_ids)} with ChEMBL IDs")

    # Get existing drug-target links
    existing_links = supabase.table('epi_drug_targets').select('drug_id, target_id').execute().data
    existing_link_set = {(l['drug_id'], l['target_id']) for l in existing_links}

    drugs_added = 0
    links_added = 0

    for symbol in PRIORITY_TARGETS:
        if symbol not in all_targets:
            print(f"\n  ⚠️ {symbol} not found in epi_targets")
            continue

        target = all_targets[symbol]
        ot_id = target.get('ot_target_id')

        if not ot_id:
            print(f"\n  ⚠️ {symbol} has no OT target ID - skipping")
            continue

        print(f"\n  📦 {symbol} ({ot_id})...")

        try:
            drugs = open_targets.fetch_known_drugs_for_target(ot_id)
            print(f"    Found {len(drugs)} drug entries")

            if not drugs:
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
                unique_drugs[drug_id]['mechanisms'].add(entry.get('mechanismOfAction', ''))
                if entry.get('disease'):
                    unique_drugs[drug_id]['diseases'].append(entry['disease'])

            print(f"    Unique drugs: {len(unique_drugs)}")

            for chembl_id, drug_data in unique_drugs.items():
                drug_name = drug_data['name']

                # Check if already exists
                if chembl_id in existing_chembl_ids or drug_name.upper() in existing_names:
                    # Just ensure drug-target link exists
                    existing_drug = supabase.table('epi_drugs').select('id').or_(
                        f"chembl_id.eq.{chembl_id},name.ilike.{drug_name}"
                    ).execute().data

                    if existing_drug:
                        drug_id = existing_drug[0]['id']
                        if (drug_id, target['id']) not in existing_link_set:
                            # Create link
                            mechanism = list(drug_data['mechanisms'])[0] if drug_data['mechanisms'] else None
                            supabase.table('epi_drug_targets').insert({
                                'drug_id': drug_id,
                                'target_id': target['id'],
                                'mechanism_of_action': mechanism
                            }).execute()
                            links_added += 1
                            existing_link_set.add((drug_id, target['id']))
                    continue

                # Insert new drug
                mechanism = list(drug_data['mechanisms'])[0] if drug_data['mechanisms'] else None

                # Determine if approved (phase 4 = approved)
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
                drug_id = result.data[0]['id']
                drugs_added += 1
                existing_chembl_ids.add(chembl_id)
                existing_names.add(drug_name.upper())

                print(f"    + {drug_name} ({chembl_id}) {'[Approved]' if is_approved else ''}")

                # Create drug-target link
                supabase.table('epi_drug_targets').insert({
                    'drug_id': drug_id,
                    'target_id': target['id'],
                    'mechanism_of_action': mechanism
                }).execute()
                links_added += 1
                existing_link_set.add((drug_id, target['id']))

        except Exception as e:
            print(f"    ✗ Error: {e}")
            import traceback
            traceback.print_exc()

    return drugs_added, links_added


def run():
    print("🧬 Pulling drugs for new epigenetic targets...")

    if not supabase:
        print("❌ Supabase client not initialized.")
        return

    # Step 1: Populate missing OT IDs
    populate_missing_ot_ids()

    # Step 2: Fetch drugs for priority targets
    drugs_added, links_added = fetch_drugs_for_targets()

    # Summary
    print("\n" + "="*50)
    print("📊 Summary:")
    print(f"  New drugs added: {drugs_added}")
    print(f"  New drug-target links: {links_added}")

    # Show drug counts by target
    print("\n📋 Drugs per target:")
    result = supabase.table('epi_drug_targets').select('target_id, epi_targets(symbol)').execute()
    target_counts = {}
    for link in result.data:
        symbol = link.get('epi_targets', {}).get('symbol', 'Unknown')
        target_counts[symbol] = target_counts.get(symbol, 0) + 1

    for symbol, count in sorted(target_counts.items(), key=lambda x: -x[1])[:20]:
        print(f"  {symbol}: {count}")

    print("\n✅ Drug pull complete!")


if __name__ == "__main__":
    run()
