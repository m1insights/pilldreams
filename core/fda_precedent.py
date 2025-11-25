"""
FDA Precedent Analysis

Calculates historical success rates by indication and phase based on existing clinical trial data.
Uses ClinicalTrials.gov data to estimate:
- Phase I → Phase II transition rate
- Phase II → Phase III transition rate
- Phase III → Approval transition rate

These rates are then used to calculate approval probability for pipeline drugs.
"""

import structlog
from typing import Dict, Any, List
from core.supabase_client import get_client
from datetime import datetime

logger = structlog.get_logger()

# Industry-standard baseline success rates (as fallback)
BASELINE_SUCCESS_RATES = {
    'Phase 1': {
        'to_phase_2': 0.63,  # 63% of Phase I trials advance to Phase II
        'to_approval': 0.095  # 9.5% overall approval rate from Phase I
    },
    'Phase 2': {
        'to_phase_3': 0.31,  # 31% of Phase II trials advance to Phase III
        'to_approval': 0.18   # 18% overall approval rate from Phase II
    },
    'Phase 3': {
        'to_approval': 0.58  # 58% of Phase III trials get approved
    }
}


def calculate_indication_success_rates(indication: str) -> Dict[str, Any]:
    """
    Calculate historical success rates for a specific indication.

    Args:
        indication: Disease/condition name

    Returns:
        Dictionary with success rates and sample sizes
    """
    client = get_client()

    # Get all trials for this indication
    trials = client.client.table('trial').select('*').ilike('condition', f'%{indication}%').execute()

    if not trials.data:
        logger.info("No trials found for indication", indication=indication)
        return {
            'indication': indication,
            'phase_1_to_2_rate': None,
            'phase_2_to_3_rate': None,
            'phase_3_to_approval_rate': None,
            'n_trials': 0,
            'uses_baseline': True
        }

    # Group trials by phase
    phase_counts = {'1': 0, '2': 0, '3': 0}
    completed_counts = {'1': 0, '2': 0, '3': 0}

    for trial in trials.data:
        phase = trial.get('phase', '')
        status = trial.get('status', '')

        if phase in phase_counts:
            phase_counts[phase] += 1
            if status in ['COMPLETED', 'TERMINATED', 'WITHDRAWN']:
                completed_counts[phase] += 1

    logger.info(f"Indication trial counts",
                indication=indication,
                phase_counts=phase_counts,
                completed_counts=completed_counts)

    # Calculate transition rates (requires longitudinal data - simplified approach)
    # In practice, you'd need to track which drugs advanced from Phase I→II→III
    # For MVP, use industry baseline adjusted by completion rate

    # Completion rate as proxy for quality
    completion_rate_p1 = completed_counts['1'] / max(phase_counts['1'], 1)
    completion_rate_p2 = completed_counts['2'] / max(phase_counts['2'], 1)
    completion_rate_p3 = completed_counts['3'] / max(phase_counts['3'], 1)

    # Adjust baseline by completion rate (higher completion = higher success)
    p1_to_p2_rate = BASELINE_SUCCESS_RATES['Phase 1']['to_phase_2'] * (0.8 + 0.2 * completion_rate_p1)
    p2_to_p3_rate = BASELINE_SUCCESS_RATES['Phase 2']['to_phase_3'] * (0.8 + 0.2 * completion_rate_p2)
    p3_approval_rate = BASELINE_SUCCESS_RATES['Phase 3']['to_approval'] * (0.8 + 0.2 * completion_rate_p3)

    return {
        'indication': indication,
        'phase_1_to_2_rate': round(p1_to_p2_rate, 3),
        'phase_2_to_3_rate': round(p2_to_p3_rate, 3),
        'phase_3_to_approval_rate': round(p3_approval_rate, 3),
        'n_trials': len(trials.data),
        'phase_1_trials': phase_counts['1'],
        'phase_2_trials': phase_counts['2'],
        'phase_3_trials': phase_counts['3'],
        'uses_baseline': False
    }


def calculate_approval_probability(drug_id: str) -> Dict[str, Any]:
    """
    Calculate approval probability for a pipeline drug.

    Combines:
    - Historical success rates for indication
    - Trial design quality scores
    - Competitive landscape position

    Args:
        drug_id: UUID of the drug

    Returns:
        Dictionary with approval probability and contributing factors
    """
    client = get_client()

    # FIRST: Check if drug is already approved
    drug_data = client.client.table('drug').select('name, is_approved, first_approval_date').eq('id', drug_id).execute()

    if drug_data.data and drug_data.data[0].get('is_approved'):
        drug_info = drug_data.data[0]
        return {
            'drug_id': drug_id,
            'is_approved': True,
            'approval_probability': 1.0,
            'current_phase': 'APPROVED',
            'first_approval_date': drug_info.get('first_approval_date'),
            'confidence': 'Confirmed',
            'reason': 'Drug is already FDA approved'
        }

    # Get drug's trials
    interventions = client.client.table('trial_intervention').select('trial_id').eq('drug_id', drug_id).execute()
    trial_ids = [i['trial_id'] for i in interventions.data] if interventions.data else []

    if not trial_ids:
        logger.info("No trials found for drug", drug_id=drug_id)
        return {
            'drug_id': drug_id,
            'is_approved': False,
            'approval_probability': 0.0,
            'confidence': 'Low',
            'reason': 'No trial data available'
        }

    trials = client.client.table('trial').select('*').in_('nct_id', trial_ids).execute()

    # Determine highest phase (exclude Phase 4 for pipeline probability calculation)
    # Phase 4 trials are post-marketing studies, not indicators of pipeline progress
    phases = [t['phase'] for t in trials.data if t.get('phase') and t.get('phase') != '4']
    phase_map = {'1': 1, '2': 2, '3': 3}
    highest_phase_num = max([phase_map.get(p, 0) for p in phases]) if phases else 0

    # If only Phase 4 trials exist, drug is likely approved
    if highest_phase_num == 0:
        phase_4_trials = [t for t in trials.data if t.get('phase') == '4']
        if phase_4_trials:
            return {
                'drug_id': drug_id,
                'is_approved': True,
                'approval_probability': 1.0,
                'current_phase': 'APPROVED',
                'confidence': 'High',
                'reason': 'Only Phase IV (post-marketing) trials found - drug is approved'
            }
        return {
            'drug_id': drug_id,
            'is_approved': False,
            'approval_probability': 0.0,
            'confidence': 'Low',
            'reason': 'No phase information'
        }

    highest_phase = {1: '1', 2: '2', 3: '3'}.get(highest_phase_num)

    # Get primary indication
    condition = trials.data[0].get('condition', 'Unknown') if trials.data else 'Unknown'

    # Get indication-specific success rates
    precedent = calculate_indication_success_rates(condition)

    # Check if drug also has Phase 4 trials (approved but still being studied)
    phase_4_trials = [t for t in trials.data if t.get('phase') == '4']
    if phase_4_trials:
        return {
            'drug_id': drug_id,
            'is_approved': True,
            'approval_probability': 1.0,
            'current_phase': 'APPROVED',
            'confidence': 'High',
            'reason': f'Drug has Phase IV trials (approved) alongside Phase {highest_phase} studies'
        }

    # Base success rate from precedent data
    if highest_phase == '1':
        base_rate = precedent['phase_1_to_2_rate'] or BASELINE_SUCCESS_RATES['Phase 1']['to_approval']
    elif highest_phase == '2':
        base_rate = precedent['phase_2_to_3_rate'] * precedent['phase_3_to_approval_rate'] if precedent['phase_2_to_3_rate'] else BASELINE_SUCCESS_RATES['Phase 2']['to_approval']
    elif highest_phase == '3':
        base_rate = precedent['phase_3_to_approval_rate'] or BASELINE_SUCCESS_RATES['Phase 3']['to_approval']
    else:
        # Should not reach here after our filtering, but just in case
        base_rate = BASELINE_SUCCESS_RATES['Phase 3']['to_approval']

    # Adjustment 1: Trial design quality
    # Get average design quality score for this drug's trials
    quality_scores = [t.get('design_quality_score') for t in trials.data if t.get('design_quality_score') is not None]

    if quality_scores:
        avg_quality = sum(quality_scores) / len(quality_scores)
        # Excellent trials (80+) get +10% boost, Poor trials (<40) get -10% penalty
        if avg_quality >= 80:
            quality_adjustment = 0.10
        elif avg_quality >= 60:
            quality_adjustment = 0.05
        elif avg_quality >= 40:
            quality_adjustment = 0.0
        else:
            quality_adjustment = -0.10
    else:
        quality_adjustment = 0.0

    # Adjustment 2: Competitive landscape
    # Get competitive advantage score
    try:
        from core.competitor_analysis import get_competitive_advantage_score
        comp_score_data = get_competitive_advantage_score(drug_id)
        comp_score = comp_score_data['score']

        # Strong position (80+) gets +5% boost, Challenging (<40) gets -5% penalty
        if comp_score >= 80:
            comp_adjustment = 0.05
        elif comp_score >= 60:
            comp_adjustment = 0.02
        elif comp_score >= 40:
            comp_adjustment = 0.0
        else:
            comp_adjustment = -0.05
    except Exception as e:
        logger.warning("Could not get competitive score", error=str(e))
        comp_adjustment = 0.0

    # Final probability (cap at 95%)
    final_probability = min(base_rate + quality_adjustment + comp_adjustment, 0.95)
    final_probability = max(final_probability, 0.01)  # Floor at 1%

    # Confidence level
    if precedent['n_trials'] >= 50:
        confidence = 'High'
    elif precedent['n_trials'] >= 20:
        confidence = 'Medium'
    else:
        confidence = 'Low'

    return {
        'drug_id': drug_id,
        'is_approved': False,
        'current_phase': highest_phase,
        'indication': condition,
        'base_success_rate': round(base_rate, 3),
        'quality_adjustment': round(quality_adjustment, 3),
        'competitive_adjustment': round(comp_adjustment, 3),
        'approval_probability': round(final_probability, 3),
        'confidence': confidence,
        'n_indication_trials': precedent['n_trials']
    }


def store_approval_probability(drug_id: str) -> bool:
    """
    Calculate and store approval probability in database.

    Args:
        drug_id: UUID of the drug

    Returns:
        True if successful
    """
    client = get_client()

    prob_data = calculate_approval_probability(drug_id)

    # Upsert to approval_probability table
    try:
        client.client.table('approval_probability').upsert({
            'drug_id': drug_id,
            'current_phase': prob_data.get('current_phase'),
            'base_success_rate': prob_data.get('base_success_rate'),
            'trial_quality_adjustment': prob_data.get('quality_adjustment'),
            'competitive_adjustment': prob_data.get('competitive_adjustment'),
            'final_probability': prob_data.get('approval_probability'),
            'confidence_level': prob_data.get('confidence'),
            'calculated_at': datetime.now().isoformat()
        }).execute()

        logger.info("Stored approval probability", drug_id=drug_id, probability=prob_data['approval_probability'])
        return True
    except Exception as e:
        logger.error("Failed to store approval probability", drug_id=drug_id, error=str(e))
        return False


if __name__ == "__main__":
    # Test with a sample drug
    client = get_client()

    # Get a drug with trials in Phase 2 or 3
    drug = client.client.table('drug').select('id, name').limit(1).execute()

    if drug.data:
        test_drug_id = drug.data[0]['id']
        test_drug_name = drug.data[0]['name']

        print(f"\n{'='*80}")
        print(f"FDA APPROVAL PROBABILITY: {test_drug_name}")
        print(f"{'='*80}\n")

        prob = calculate_approval_probability(test_drug_id)

        print(f"Current Phase: {prob['current_phase']}")
        print(f"Indication: {prob['indication']}")
        print(f"\nBase Success Rate: {prob['base_success_rate']*100:.1f}%")
        print(f"Trial Quality Adjustment: {prob['quality_adjustment']*100:+.1f}%")
        print(f"Competitive Adjustment: {prob['competitive_adjustment']*100:+.1f}%")
        print(f"\n✅ FINAL APPROVAL PROBABILITY: {prob['approval_probability']*100:.1f}%")
        print(f"Confidence Level: {prob['confidence']}")
        print(f"Based on {prob['n_indication_trials']} trials in this indication\n")

        print(f"{'='*80}\n")
