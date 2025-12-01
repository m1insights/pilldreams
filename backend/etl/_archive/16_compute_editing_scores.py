"""
ETL Script: Compute scores for epigenetic editing assets.
Uses rule-based scoring for modality and durability.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from backend.etl.supabase_client import supabase
from backend.etl import open_targets

# Modality scoring rules
MODALITY_SCORES = {
    # delivery_type + dbd_type + effector_combo -> score
    'LNP_mRNA_CRISPR_dCas9_combo': 90,
    'LNP_mRNA_TALE_combo': 85,
    'LNP_mRNA_ZF_combo': 80,
    'AAV_CRISPR_dCas9_combo': 75,
    'AAV_CRISPR_dCas9_eraser': 65,
    'AAV_ZF_combo': 70,
    'LNP_mRNA_base_editor_eraser': 60,  # Base editing (not pure epigenetic)
    'LNP_mRNA_CRISPR_dCas9_indirect_repressor': 70,
}

# Durability scoring (based on known preclinical data)
DURABILITY_KEYWORDS = {
    'NHP': 90,  # Non-human primate data
    '>1 year': 95,
    '1 year': 90,
    '6 month': 75,
    'mouse': 60,
    'in vitro': 40,
}


def compute_modality_score(asset: dict) -> float:
    """Compute modality score based on delivery, DBD, and effector type."""
    delivery = asset.get('delivery_type', '').upper()
    dbd = asset.get('dbd_type', '').upper()
    effector = asset.get('effector_type', '').lower()

    # Build key
    key = f"{delivery}_{dbd}_{effector}"

    # Try exact match
    for pattern, score in MODALITY_SCORES.items():
        if pattern.upper() == key:
            return score

    # Fallback scoring
    score = 50  # base

    # Delivery bonus
    if 'LNP' in delivery:
        score += 15
    elif 'AAV' in delivery:
        score += 10

    # DBD bonus
    if 'CRISPR' in dbd:
        score += 10
    elif 'TALE' in dbd:
        score += 8
    elif 'ZF' in dbd:
        score += 5

    # Effector bonus
    effector_domains = asset.get('effector_domains', []) or []
    if isinstance(effector_domains, str):
        effector_domains = [effector_domains]

    if 'DNMT3A' in effector_domains and 'DNMT3L' in effector_domains:
        score += 15  # Full methylation machinery
    elif 'DNMT3A' in effector_domains:
        score += 10
    if 'KRAB' in effector_domains or any('KRAB' in d for d in effector_domains):
        score += 5

    return min(100, score)


def compute_durability_score(asset: dict) -> float:
    """Compute durability score based on description keywords."""
    description = (asset.get('description') or '').lower()
    status = (asset.get('status') or '').lower()

    # Check for keywords
    for keyword, score in DURABILITY_KEYWORDS.items():
        if keyword.lower() in description:
            return score

    # Status-based fallback
    if status == 'clinical' or asset.get('phase'):
        return 70  # Clinical stage implies some durability data
    elif status == 'preclinical':
        return 50

    return 40  # Unknown


def run():
    print("🧬 Computing editing asset scores...")

    if not supabase:
        print("❌ Supabase client not initialized.")
        return

    # Get all editing assets
    assets = supabase.table('epi_editing_assets').select('*').execute().data

    if not assets:
        print("⚠️ No editing assets found")
        return

    print(f"📦 Found {len(assets)} editing assets")

    for asset in assets:
        name = asset['name']
        asset_id = asset['id']
        print(f"\n📊 Scoring: {name}")

        # Get indication_id (handle different column names)
        indication_id = asset.get('indication_id') or asset.get('primary_indication_id')
        target_id = asset.get('target_gene_id') or asset.get('target_id')

        # 1. Target Biology Score (from Open Targets if available)
        target_bio_score = 0
        if target_id and indication_id:
            # Get target's OT ID
            target_info = supabase.table('epi_targets').select('ot_target_id, symbol').eq('id', target_id).execute().data
            indication_info = supabase.table('epi_indications').select('efo_id').eq('id', indication_id).execute().data

            if target_info and indication_info:
                ot_target_id = target_info[0].get('ot_target_id')
                efo_id = indication_info[0].get('efo_id')

                if ot_target_id and efo_id:
                    try:
                        disease_scores = open_targets.fetch_disease_targets_scores(efo_id)
                        raw_score = disease_scores.get(ot_target_id, 0)
                        target_bio_score = min(100, raw_score * 100)
                        print(f"    Target bio score: {target_bio_score:.1f}")
                    except Exception as e:
                        print(f"    ⚠️ OT API error: {e}")

        # 2. Editing Modality Score
        modality_score = compute_modality_score(asset)
        print(f"    Modality score: {modality_score:.1f}")

        # 3. Durability Score
        durability_score = compute_durability_score(asset)
        print(f"    Durability score: {durability_score:.1f}")

        # 4. Total Score (weighted)
        # Formula: 50% bio + 30% modality + 20% durability
        total_score = (0.5 * target_bio_score) + (0.3 * modality_score) + (0.2 * durability_score)
        print(f"    Total score: {total_score:.1f}")

        # Upsert score
        score_data = {
            'editing_asset_id': asset_id,
            'indication_id': indication_id,
            'target_bio_score': target_bio_score,
            'editing_modality_score': modality_score,
            'durability_score': durability_score,
            'total_editing_score': total_score,
        }

        # Check if exists
        existing = supabase.table('epi_editing_scores').select('id').eq('editing_asset_id', asset_id).execute()

        if existing.data:
            supabase.table('epi_editing_scores').update(score_data).eq('editing_asset_id', asset_id).execute()
            print(f"  ✅ Updated score for {name}")
        else:
            supabase.table('epi_editing_scores').insert(score_data).execute()
            print(f"  ✅ Inserted score for {name}")

    # Summary
    scores = supabase.table('epi_editing_scores').select('total_editing_score').execute().data
    if scores:
        avg = sum(s['total_editing_score'] or 0 for s in scores) / len(scores)
        max_score = max(s['total_editing_score'] or 0 for s in scores)
        min_score = min(s['total_editing_score'] or 0 for s in scores)
        print(f"\n📊 Score Summary:")
        print(f"  Count: {len(scores)}")
        print(f"  Avg: {avg:.1f}")
        print(f"  Min: {min_score:.1f}")
        print(f"  Max: {max_score:.1f}")

    print("\n✅ Editing score computation complete!")


if __name__ == "__main__":
    run()
