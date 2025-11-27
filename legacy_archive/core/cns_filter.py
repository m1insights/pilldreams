"""
CNS/Neuro Drug Filter

Filters the drug database to only show CNS/psychiatric drugs based on:
1. Trial conditions (depression, anxiety, schizophrenia, etc.)
2. Target binding data (serotonin, dopamine, GABA receptors, etc.)

This creates a focused "CNS Drug Intelligence Platform" view.
"""

from typing import Set, List, Dict, Any
from functools import lru_cache
import structlog

logger = structlog.get_logger()

# CNS-related conditions to search for in trial data
CNS_CONDITIONS = [
    'depression', 'depressive', 'anxiety', 'anxious', 'schizophrenia', 'psychosis', 'psychotic',
    'bipolar', 'mania', 'adhd', 'attention deficit', 'alzheimer', 'dementia', 'parkinson',
    'epilepsy', 'seizure', 'multiple sclerosis', 'migraine', 'headache', 'insomnia', 'sleep',
    'ocd', 'obsessive', 'ptsd', 'trauma', 'autism', 'huntington', 'als', 'amyotrophic',
    'neuropath', 'pain', 'fibromyalgia', 'addiction', 'substance use', 'alcohol use',
    'opioid use', 'smoking cessation', 'nicotine', 'major depressive', 'generalized anxiety',
    'social anxiety', 'panic disorder', 'cognitive', 'memory', 'neurodegenerative'
]

# CNS-related targets (receptors, transporters, enzymes)
CNS_TARGET_KEYWORDS = [
    'serotonin', '5-ht', '5-hydroxytryptamine', 'dopamine', 'gaba', 'glutamate', 'nmda',
    'acetylcholine', 'nicotinic', 'muscarinic', 'norepinephrine', 'adrenergic',
    'opioid', 'cannabinoid', 'histamine', 'melatonin', 'orexin', 'sigma',
    'monoamine', 'vesicular', 'ampa', 'kainate', 'glycine receptor'
]


def get_cns_drug_ids(db_client) -> Set[str]:
    """
    Get all drug IDs that are CNS/neuro related.

    Combines two methods:
    1. Drugs in trials for CNS conditions
    2. Drugs with CNS target bindings

    Args:
        db_client: Supabase client instance

    Returns:
        Set of drug UUIDs that are CNS-related
    """
    cns_drug_ids = set()

    # Method 1: Get drugs by trial condition
    condition_drug_ids = _get_drugs_by_condition(db_client)
    cns_drug_ids.update(condition_drug_ids)
    logger.info(f"CNS drugs by condition: {len(condition_drug_ids)}")

    # Method 2: Get drugs by target binding
    target_drug_ids = _get_drugs_by_target(db_client)
    cns_drug_ids.update(target_drug_ids)
    logger.info(f"CNS drugs by target: {len(target_drug_ids)}")

    logger.info(f"Total unique CNS drugs: {len(cns_drug_ids)}")
    return cns_drug_ids


def _get_drugs_by_condition(db_client) -> Set[str]:
    """Get drug IDs from trials with CNS-related conditions."""
    drug_ids = set()

    # Fetch all trials with pagination
    all_trials = []
    offset = 0
    batch_size = 1000

    while True:
        batch = db_client.client.table('trial').select('nct_id, condition').range(offset, offset + batch_size - 1).execute()
        if not batch.data:
            break
        all_trials.extend(batch.data)
        offset += batch_size
        if len(batch.data) < batch_size:
            break

    # Find CNS-related trial IDs
    cns_trial_ids = set()
    for trial in all_trials:
        condition = (trial.get('condition') or '').lower()
        for cns_term in CNS_CONDITIONS:
            if cns_term in condition:
                cns_trial_ids.add(trial['nct_id'])
                break

    # Get drug IDs from these trials via trial_intervention junction
    cns_trial_list = list(cns_trial_ids)
    for i in range(0, len(cns_trial_list), 500):
        batch_ids = cns_trial_list[i:i+500]
        interventions = db_client.client.table('trial_intervention').select('drug_id').in_('trial_id', batch_ids).execute()
        drug_ids.update(d['drug_id'] for d in interventions.data if d.get('drug_id'))

    return drug_ids


def _get_drugs_by_target(db_client) -> Set[str]:
    """Get drug IDs that bind to CNS-related targets."""
    drug_ids = set()

    # Fetch all targets with pagination
    all_targets = []
    offset = 0
    batch_size = 1000

    while True:
        batch = db_client.client.table('target').select('id, name').range(offset, offset + batch_size - 1).execute()
        if not batch.data:
            break
        all_targets.extend(batch.data)
        offset += batch_size
        if len(batch.data) < batch_size:
            break

    # Find CNS-related target IDs
    cns_target_ids = set()
    for target in all_targets:
        name = (target.get('name') or '').lower()
        for keyword in CNS_TARGET_KEYWORDS:
            if keyword in name:
                cns_target_ids.add(target['id'])
                break

    # Get drug IDs that bind to these targets
    target_list = list(cns_target_ids)
    for i in range(0, len(target_list), 100):
        batch_ids = target_list[i:i+100]
        bindings = db_client.client.table('drugtarget').select('drug_id').in_('target_id', batch_ids).execute()
        drug_ids.update(d['drug_id'] for d in bindings.data if d.get('drug_id'))

    return drug_ids


def is_cns_drug(drug_id: str, cns_drug_ids: Set[str]) -> bool:
    """
    Check if a drug is CNS-related.

    Args:
        drug_id: UUID of the drug
        cns_drug_ids: Pre-computed set of CNS drug IDs

    Returns:
        True if drug is CNS-related
    """
    return drug_id in cns_drug_ids


def filter_cns_drugs(drugs: List[Dict[str, Any]], cns_drug_ids: Set[str]) -> List[Dict[str, Any]]:
    """
    Filter a list of drugs to only include CNS-related ones.

    Args:
        drugs: List of drug dictionaries
        cns_drug_ids: Pre-computed set of CNS drug IDs

    Returns:
        Filtered list of CNS drugs only
    """
    return [d for d in drugs if d.get('id') in cns_drug_ids]


def get_cns_stats(db_client, cns_drug_ids: Set[str]) -> Dict[str, int]:
    """
    Get statistics for CNS drugs.

    Args:
        db_client: Supabase client instance
        cns_drug_ids: Pre-computed set of CNS drug IDs

    Returns:
        Dictionary with CNS drug statistics
    """
    # Get CNS trials count
    all_trials = []
    offset = 0
    while True:
        batch = db_client.client.table('trial').select('nct_id, condition').range(offset, offset + 1000 - 1).execute()
        if not batch.data:
            break
        all_trials.extend(batch.data)
        offset += 1000
        if len(batch.data) < 1000:
            break

    cns_trial_count = 0
    for trial in all_trials:
        condition = (trial.get('condition') or '').lower()
        for cns_term in CNS_CONDITIONS:
            if cns_term in condition:
                cns_trial_count += 1
                break

    return {
        'total_cns_drugs': len(cns_drug_ids),
        'total_cns_trials': cns_trial_count
    }
