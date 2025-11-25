"""
Competitive Landscape Analysis

Identifies competing drugs and calculates market position based on:
- Drugs targeting the same indication
- Drugs sharing molecular targets
- Phase advancement vs competitors
- Unique vs crowded target space
"""

import structlog
from typing import Dict, List, Any, Optional
from core.supabase_client import get_client

logger = structlog.get_logger()


def get_competitors_by_indication(drug_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Find drugs targeting the same indication(s).

    Args:
        drug_id: UUID of the drug to analyze
        limit: Maximum number of competitors to return

    Returns:
        List of competing drugs with trial information
    """
    client = get_client()

    # Get this drug's conditions
    drug_trials = client.client.table('trial').select('condition').eq('drug_id', drug_id).execute()

    if not drug_trials.data:
        logger.info("No trials found for drug", drug_id=drug_id)
        return []

    # Extract unique conditions
    conditions = list(set([t['condition'] for t in drug_trials.data if t.get('condition')]))

    if not conditions:
        return []

    logger.info(f"Found {len(conditions)} unique conditions for drug", drug_id=drug_id)

    # Find all other drugs targeting these conditions
    competitors = []

    for condition in conditions[:5]:  # Limit to top 5 conditions
        # Query trials with same condition, different drug
        competing_trials = client.client.table('trial').select(
            'drug_id, phase, status, condition'
        ).eq('condition', condition).neq('drug_id', drug_id).execute()

        if competing_trials.data:
            # Group by drug_id
            drug_phases = {}
            for trial in competing_trials.data:
                did = trial['drug_id']
                if did not in drug_phases:
                    drug_phases[did] = {
                        'drug_id': did,
                        'condition': condition,
                        'phases': set(),
                        'statuses': set(),
                        'trial_count': 0
                    }
                drug_phases[did]['phases'].add(trial['phase'])
                drug_phases[did]['statuses'].add(trial['status'])
                drug_phases[did]['trial_count'] += 1

            # Get drug names
            for did, info in drug_phases.items():
                drug_info = client.client.table('drug').select('name').eq('id', did).execute()
                if drug_info.data:
                    info['drug_name'] = drug_info.data[0]['name']
                    info['highest_phase'] = max(info['phases'], key=lambda p: {'I': 1, 'II': 2, 'III': 3, 'IV': 4}.get(p, 0))
                    competitors.append(info)

    # Remove duplicates and sort by phase
    unique_competitors = {c['drug_id']: c for c in competitors}.values()
    sorted_competitors = sorted(
        unique_competitors,
        key=lambda x: {'I': 1, 'II': 2, 'III': 3, 'IV': 4}.get(x['highest_phase'], 0),
        reverse=True
    )

    logger.info(f"Found {len(sorted_competitors)} competing drugs", drug_id=drug_id)

    return list(sorted_competitors)[:limit]


def get_competitors_by_target(drug_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Find drugs sharing the same molecular targets.

    Args:
        drug_id: UUID of the drug to analyze
        limit: Maximum number of competitors to return

    Returns:
        List of drugs sharing targets
    """
    client = get_client()

    # Get this drug's targets
    drug_targets = client.client.table('drugtarget').select(
        'target_id, affinity_value'
    ).eq('drug_id', drug_id).execute()

    if not drug_targets.data:
        logger.info("No targets found for drug", drug_id=drug_id)
        return []

    target_ids = [t['target_id'] for t in drug_targets.data]

    logger.info(f"Found {len(target_ids)} targets for drug", drug_id=drug_id)

    # Find other drugs targeting the same targets
    competitors = []

    for target_id in target_ids[:10]:  # Limit to top 10 targets
        competing_bindings = client.client.table('drugtarget').select(
            'drug_id, affinity_value, target_id'
        ).eq('target_id', target_id).neq('drug_id', drug_id).execute()

        if competing_bindings.data:
            for binding in competing_bindings.data:
                # Get drug info
                drug_info = client.client.table('drug').select('name').eq('id', binding['drug_id']).execute()

                # Get target info
                target_info = client.client.table('target').select('symbol, description').eq('id', binding['target_id']).execute()

                if drug_info.data and target_info.data:
                    competitors.append({
                        'drug_id': binding['drug_id'],
                        'drug_name': drug_info.data[0]['name'],
                        'target_id': binding['target_id'],
                        'target_symbol': target_info.data[0]['symbol'],
                        'target_description': target_info.data[0].get('description', ''),
                        'affinity_value': binding.get('affinity_value')
                    })

    # Remove duplicates
    unique_competitors = {c['drug_id']: c for c in competitors}.values()

    logger.info(f"Found {len(unique_competitors)} drugs sharing targets", drug_id=drug_id)

    return list(unique_competitors)[:limit]


def get_competitive_advantage_score(drug_id: str) -> Dict[str, Any]:
    """
    Calculate competitive advantage score based on market position.

    Args:
        drug_id: UUID of the drug to analyze

    Returns:
        Dictionary with scores and analysis
    """
    client = get_client()

    # Get drug trials
    drug_trials = client.client.table('trial').select('phase, status').eq('drug_id', drug_id).execute()

    if not drug_trials.data:
        return {
            'score': 0,
            'category': 'Unknown',
            'reason': 'No trial data available'
        }

    # Calculate highest phase
    phases = [t['phase'] for t in drug_trials.data if t.get('phase')]
    phase_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4}
    highest_phase_num = max([phase_map.get(p, 0) for p in phases]) if phases else 0
    highest_phase = {1: 'I', 2: 'II', 3: 'III', 4: 'IV'}.get(highest_phase_num, 'Unknown')

    # Get competitors
    indication_competitors = get_competitors_by_indication(drug_id)
    target_competitors = get_competitors_by_target(drug_id)

    # Calculate scores
    score = 50  # Base score

    # Phase advancement (+30 max)
    score += highest_phase_num * 7.5

    # Market crowding penalty
    if len(indication_competitors) == 0:
        score += 20  # Blue ocean
        market_position = "Blue Ocean - No direct competitors"
    elif len(indication_competitors) <= 3:
        score += 10  # Low competition
        market_position = "Low Competition"
    elif len(indication_competitors) <= 10:
        score += 0  # Moderate competition
        market_position = "Moderate Competition"
    else:
        score -= 10  # Crowded market
        market_position = "Crowded Market"

    # Target uniqueness bonus
    if len(target_competitors) == 0:
        score += 10  # Novel target
    elif len(target_competitors) <= 2:
        score += 5  # Somewhat unique

    # Phase leadership vs competitors
    if indication_competitors:
        competitor_phases = [
            phase_map.get(c.get('highest_phase', 'I'), 0)
            for c in indication_competitors
        ]
        max_competitor_phase = max(competitor_phases) if competitor_phases else 0

        if highest_phase_num > max_competitor_phase:
            score += 10  # Phase leader
            leadership = "Phase Leader"
        elif highest_phase_num == max_competitor_phase:
            leadership = "Tied for Lead"
        else:
            score -= 5  # Behind competitors
            leadership = "Behind Competitors"
    else:
        leadership = "No Competitors"

    # Cap score at 100
    final_score = min(max(score, 0), 100)

    # Categorize
    if final_score >= 80:
        category = "Strong Position"
    elif final_score >= 60:
        category = "Favorable Position"
    elif final_score >= 40:
        category = "Competitive Position"
    else:
        category = "Challenging Position"

    return {
        'score': int(final_score),
        'category': category,
        'highest_phase': highest_phase,
        'indication_competitors': len(indication_competitors),
        'target_competitors': len(target_competitors),
        'market_position': market_position,
        'phase_leadership': leadership
    }


def get_full_competitive_landscape(drug_id: str) -> Dict[str, Any]:
    """
    Get complete competitive landscape analysis.

    Args:
        drug_id: UUID of the drug to analyze

    Returns:
        Complete competitive analysis
    """
    indication_competitors = get_competitors_by_indication(drug_id)
    target_competitors = get_competitors_by_target(drug_id)
    advantage_score = get_competitive_advantage_score(drug_id)

    return {
        'indication_competitors': indication_competitors,
        'target_competitors': target_competitors,
        'competitive_advantage': advantage_score
    }


if __name__ == "__main__":
    # Test with a sample drug
    client = get_client()

    # Get a drug with trials
    drug = client.client.table('drug').select('id, name').limit(1).execute()

    if drug.data:
        test_drug_id = drug.data[0]['id']
        test_drug_name = drug.data[0]['name']

        print(f"\n{'='*80}")
        print(f"COMPETITIVE LANDSCAPE ANALYSIS: {test_drug_name}")
        print(f"{'='*80}\n")

        landscape = get_full_competitive_landscape(test_drug_id)

        print(f"Competitive Advantage Score: {landscape['competitive_advantage']['score']}/100")
        print(f"Category: {landscape['competitive_advantage']['category']}")
        print(f"Market Position: {landscape['competitive_advantage']['market_position']}")
        print(f"Phase Leadership: {landscape['competitive_advantage']['phase_leadership']}\n")

        print(f"Indication Competitors: {len(landscape['indication_competitors'])}")
        if landscape['indication_competitors']:
            print("\nTop 5 Competitors by Indication:")
            for i, comp in enumerate(landscape['indication_competitors'][:5], 1):
                print(f"  {i}. {comp['drug_name']} - Phase {comp['highest_phase']} ({comp['trial_count']} trials)")

        print(f"\nTarget Competitors: {len(landscape['target_competitors'])}")
        if landscape['target_competitors']:
            print("\nTop 5 Drugs Sharing Targets:")
            for i, comp in enumerate(landscape['target_competitors'][:5], 1):
                print(f"  {i}. {comp['drug_name']} - {comp['target_symbol']}")

        print(f"\n{'='*80}\n")
