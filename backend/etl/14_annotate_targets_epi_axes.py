"""
ETL Script: Annotate targets with IO exhaustion axis, resistance roles, and aging clock relevance.
Also inserts new targets (NSD2, METTL7A, YTHDF1, H2AFY, etc.)
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from backend.etl.supabase_client import supabase

# IO Exhaustion Axis targets (T-cell exhaustion, immunomodulation)
IO_EXHAUSTION_TARGETS = [
    'DNMT3A', 'TET2', 'SUV39H1', 'EZH2', 'EZH1',
    'EED', 'SUZ12',  # PRC2 components
    'EP300',  # p300
    'KAT2A',  # GCN5
    'ASXL1'
]

# Epigenetic resistance role mappings
EPI_RESISTANCE_ROLES = {
    'METTL7A': 'LUAD_TKI_resistance',
    'YTHDF1': 'HCC_epi_io',
    'H2AFY': 'TOP1_sensitivity',
    'SUV39H1': 'MB_radiation_resistance',
}

# Aging clock relevance
AGING_CLOCK_RELEVANCE = {
    'DNMT3A': 'atlas_marker',
    'TET2': 'atlas_marker',
    'DNMT1': 'atlas_marker',
}

# New targets to insert
NEW_TARGETS = [
    {
        'symbol': 'NSD2',
        'full_name': 'Nuclear receptor binding SET domain protein 2 (WHSC1/MMSET)',
        'family': 'HMT',
        'class': 'writer',
        'is_core_epigenetic': True,
        'io_exhaustion_axis': False,
        'epi_resistance_role': None,
    },
    {
        'symbol': 'METTL7A',
        'full_name': 'Methyltransferase like 7A',
        'family': 'other',
        'class': 'chromatin_regulator',
        'is_core_epigenetic': False,
        'io_exhaustion_axis': False,
        'epi_resistance_role': 'LUAD_TKI_resistance',
    },
    {
        'symbol': 'YTHDF1',
        'full_name': 'YTH N6-methyladenosine RNA binding protein 1',
        'family': 'm6A_reader',
        'class': 'reader',
        'is_core_epigenetic': False,
        'io_exhaustion_axis': False,
        'epi_resistance_role': 'HCC_epi_io',
    },
    {
        'symbol': 'H2AFY',
        'full_name': 'H2A histone family member Y (macroH2A1)',
        'family': 'histone_variant',
        'class': 'reader',
        'is_core_epigenetic': False,
        'io_exhaustion_axis': False,
        'epi_resistance_role': 'TOP1_sensitivity',
    },
    {
        'symbol': 'PCSK9',
        'full_name': 'Proprotein convertase subtilisin/kexin type 9',
        'family': 'metabolic',
        'class': 'other',
        'is_core_epigenetic': False,
        'io_exhaustion_axis': False,
        'epi_resistance_role': None,
    },
    {
        'symbol': 'MYC',
        'full_name': 'MYC proto-oncogene',
        'family': 'transcription_factor',
        'class': 'other',
        'is_core_epigenetic': False,
        'io_exhaustion_axis': False,
        'epi_resistance_role': None,
    },
    {
        'symbol': 'DUX4',
        'full_name': 'Double homeobox 4',
        'family': 'transcription_factor',
        'class': 'other',
        'is_core_epigenetic': False,
        'io_exhaustion_axis': False,
        'epi_resistance_role': None,
    },
    {
        'symbol': 'EP300',
        'full_name': 'E1A binding protein p300',
        'family': 'HAT',
        'class': 'writer',
        'is_core_epigenetic': True,
        'io_exhaustion_axis': True,
        'epi_resistance_role': None,
    },
    {
        'symbol': 'KAT2A',
        'full_name': 'Lysine acetyltransferase 2A (GCN5)',
        'family': 'HAT',
        'class': 'writer',
        'is_core_epigenetic': True,
        'io_exhaustion_axis': True,
        'epi_resistance_role': None,
    },
    {
        'symbol': 'ASXL1',
        'full_name': 'ASXL transcriptional regulator 1',
        'family': 'PRC',
        'class': 'scaffold',
        'is_core_epigenetic': True,
        'io_exhaustion_axis': True,
        'epi_resistance_role': None,
    },
]


def run():
    print("🧬 Annotating targets with epi axes...")

    if not supabase:
        print("❌ Supabase client not initialized.")
        return

    # 1. Insert new targets
    print("\n📥 Inserting new targets...")
    for target in NEW_TARGETS:
        # Check if exists
        existing = supabase.table('epi_targets').select('id').eq('symbol', target['symbol']).execute()
        if existing.data:
            print(f"  ⏭️ {target['symbol']} already exists, updating annotations...")
            update_data = {k: v for k, v in target.items() if k not in ['symbol', 'full_name', 'family', 'class', 'is_core_epigenetic']}
            if update_data:
                supabase.table('epi_targets').update(update_data).eq('symbol', target['symbol']).execute()
        else:
            print(f"  ➕ Inserting {target['symbol']}...")
            supabase.table('epi_targets').insert(target).execute()

    # 2. Update IO exhaustion axis
    print("\n🔄 Updating IO exhaustion axis...")
    for symbol in IO_EXHAUSTION_TARGETS:
        result = supabase.table('epi_targets').update({
            'io_exhaustion_axis': True
        }).eq('symbol', symbol).execute()
        if result.data:
            print(f"  ✅ {symbol}: io_exhaustion_axis=TRUE")
        else:
            print(f"  ⚠️ {symbol}: not found")

    # 3. Update resistance roles
    print("\n🔄 Updating epi_resistance_role...")
    for symbol, role in EPI_RESISTANCE_ROLES.items():
        result = supabase.table('epi_targets').update({
            'epi_resistance_role': role
        }).eq('symbol', symbol).execute()
        if result.data:
            print(f"  ✅ {symbol}: epi_resistance_role={role}")

    # 4. Update aging clock relevance
    print("\n🔄 Updating aging_clock_relevance...")
    for symbol, relevance in AGING_CLOCK_RELEVANCE.items():
        result = supabase.table('epi_targets').update({
            'aging_clock_relevance': relevance
        }).eq('symbol', symbol).execute()
        if result.data:
            print(f"  ✅ {symbol}: aging_clock_relevance={relevance}")

    # 5. Summary
    print("\n📊 Summary:")
    targets = supabase.table('epi_targets').select('symbol, io_exhaustion_axis, epi_resistance_role, aging_clock_relevance').execute().data
    io_count = sum(1 for t in targets if t.get('io_exhaustion_axis'))
    resist_count = sum(1 for t in targets if t.get('epi_resistance_role'))
    aging_count = sum(1 for t in targets if t.get('aging_clock_relevance'))
    print(f"  Total targets: {len(targets)}")
    print(f"  IO exhaustion axis: {io_count}")
    print(f"  Epi resistance role: {resist_count}")
    print(f"  Aging clock relevance: {aging_count}")

    print("\n✅ Target annotation complete!")


if __name__ == "__main__":
    run()
