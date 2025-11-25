"""
Drug Display Utilities

Helper functions for presenting drug data in the UI with smart deduplication
and normalization for better user experience.
"""

from typing import List, Dict
from core.drug_name_utils import normalize_drug_name


def get_unique_drugs(drugs_list: List[Dict]) -> List[Dict]:
    """
    Deduplicate drugs by normalized name for cleaner UI display.

    Takes a list of drug records from database and returns a deduplicated list
    where drugs with the same normalized name are collapsed into a single entry.

    Args:
        drugs_list: List of drug dicts with 'id' and 'name' keys

    Returns:
        List of deduplicated drug dicts with keys:
        - id: Drug ID (from first variant)
        - name: Original raw name (from first variant)
        - display_name: Normalized name (what user sees)
        - variants: List of all raw names that map to this normalized name
        - variant_count: Number of dosage/formulation variants

    Example:
        Input: [
            {'id': '1', 'name': 'Metformin 500mg'},
            {'id': '2', 'name': 'Metformin 850mg'},
            {'id': '3', 'name': 'Aspirin'}
        ]

        Output: [
            {
                'id': '1',
                'name': 'Metformin 500mg',
                'display_name': 'Metformin',
                'variants': ['Metformin 500mg', 'Metformin 850mg'],
                'variant_count': 2
            },
            {
                'id': '3',
                'name': 'Aspirin',
                'display_name': 'Aspirin',
                'variants': ['Aspirin'],
                'variant_count': 1
            }
        ]
    """
    normalized_map = {}

    for drug in drugs_list:
        normalized = normalize_drug_name(drug['name'])

        # Skip empty normalized names (shouldn't happen, but defensive)
        if not normalized or normalized.strip() == '':
            normalized = drug['name']  # Fallback to original

        if normalized not in normalized_map:
            # First occurrence - create entry
            normalized_map[normalized] = {
                'id': drug['id'],  # Use first occurrence's ID
                'name': drug['name'],  # Original raw name
                'display_name': normalized,  # What user sees in dropdown
                'variants': [drug['name']],
                'variant_count': 1
            }
        else:
            # Subsequent occurrence - track variant but don't duplicate
            normalized_map[normalized]['variants'].append(drug['name'])
            normalized_map[normalized]['variant_count'] += 1

    return list(normalized_map.values())


def format_variant_info(variant_count: int) -> str:
    """
    Format variant count for display.

    Args:
        variant_count: Number of dosage/formulation variants

    Returns:
        Formatted string like "3 dosage variants" or empty string if 1
    """
    if variant_count <= 1:
        return ""
    elif variant_count == 2:
        return "2 dosage variants"
    else:
        return f"{variant_count} dosage variants"


def should_show_variant_info(drug: Dict) -> bool:
    """
    Determine if we should show variant information to user.

    Args:
        drug: Drug dict from get_unique_drugs()

    Returns:
        True if drug has multiple variants and we should inform user
    """
    return drug.get('variant_count', 1) > 1
