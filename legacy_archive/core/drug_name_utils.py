"""
Drug Name Normalization Utilities

Cleans and normalizes drug names for consistent API queries across
ChEMBL, PubMed, OpenFDA, etc.
"""

import re
from typing import Optional


def normalize_drug_name(name: str) -> str:
    """
    Normalize drug name by removing dosage information and standardizing format.

    Examples:
        "Cilostazol 100 MG" -> "Cilostazol"
        "Minocycline 100mg" -> "Minocycline"
        "Aspirin 81 mg" -> "Aspirin"
        "VMD-928 300" -> "VMD-928" (keeps numeric part of compound ID)
        "Paclitaxel 175 mg/m2" -> "Paclitaxel"

    Args:
        name: Raw drug name from clinical trial data

    Returns:
        Normalized drug name suitable for API queries
    """
    if not name:
        return name

    # Common dosage patterns to remove
    dosage_patterns = [
        r'\s*\d+\.?\d*\s*(mg|mcg|µg|ug|g|gram|grams)\b',  # 100 mg, 2.5 mcg
        r'\s*\d+\.?\d*\s*(ml|mL)\b',  # 10 ml
        r'\s*\d+\.?\d*\s*(mg|mcg)/m2?\b',  # 100 mg/m2
        r'\s*\d+\.?\d*\s*(mg|mcg)/(kg|day)\b',  # 5 mg/kg
        r'\s*\d+\.?\d*\s*%',  # 5%
        r'\s*\d+\.?\d*\s*(unit|units|iu|IU)\b',  # 1000 units
        r'\s*\d+\.?\d*\s*(dose|doses)\b',  # 3 doses
    ]

    # Apply all dosage pattern removals
    cleaned = name
    for pattern in dosage_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    # Remove trailing numbers that look like dosages (but keep compound IDs)
    # Only remove if preceded by space and is just a number
    # Keeps "VMD-928" but removes "Aspirin 81"
    cleaned = re.sub(r'\s+\d+\.?\d*$', '', cleaned)

    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # Remove common trailing descriptors
    trailing_to_remove = [
        r'\s+(tablet|tablets|capsule|capsules|cap|caps)\b',
        r'\s+(oral|injection|IV|IM|SC|topical)\b',
        r'\s+(solution|suspension|powder)\b',
    ]

    for pattern in trailing_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    # Final cleanup
    cleaned = cleaned.strip()

    return cleaned


def get_base_drug_name(name: str) -> Optional[str]:
    """
    Extract the base drug name, ignoring combinations and adjuvants.

    Examples:
        "Adjuvant temozolomide" -> "temozolomide"
        "Bevacizumab plus Paclitaxel" -> "Bevacizumab"
        "Placebo" -> None (not a real drug)

    Args:
        name: Drug name (possibly normalized)

    Returns:
        Base drug name, or None if it's a placebo/control
    """
    if not name:
        return None

    # Filter out obvious non-drugs
    non_drugs = ['placebo', 'control', 'standard care', 'sham', 'vehicle']
    if any(nd in name.lower() for nd in non_drugs):
        return None

    # Remove common prefixes
    prefixes_to_remove = [
        r'^adjuvant\s+',
        r'^neoadjuvant\s+',
        r'^maintenance\s+',
        r'^concurrent\s+',
    ]

    cleaned = name
    for pattern in prefixes_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    # If it's a combination (contains "plus", "+", "and"), take first drug
    if any(sep in cleaned.lower() for sep in [' plus ', '+', ' and ', '/']):
        # Split and take first component
        for sep in [' plus ', '+', ' and ', '/']:
            if sep in cleaned.lower():
                parts = re.split(re.escape(sep), cleaned, flags=re.IGNORECASE)
                if parts:
                    cleaned = parts[0].strip()
                break

    return cleaned.strip()


def should_query_external_apis(name: str) -> bool:
    """
    Determine if this drug name should be queried against external APIs.

    Filters out placebos, gene therapy constructs, and other non-standard drugs
    that won't be found in ChEMBL/PubMed/OpenFDA.

    Args:
        name: Drug name

    Returns:
        True if should query external APIs, False otherwise
    """
    if not name:
        return False

    name_lower = name.lower()

    # Skip placebos and controls
    if any(term in name_lower for term in ['placebo', 'control', 'sham', 'vehicle']):
        return False

    # Skip gene therapy constructs (very long names with technical details)
    if any(term in name_lower for term in ['gene modified', 'chimeric antigen receptor', 'car t']):
        return False

    # Skip obvious combinations (these should be queried as individual drugs)
    if name_lower.count('+') > 2:  # More than 2 pluses indicates complex combo
        return False

    # Skip immunotherapy (too generic)
    if name_lower == 'immunotherapy':
        return False

    return True


def get_queryable_drug_names(raw_name: str) -> list[str]:
    """
    Get all queryable drug names from a raw clinical trial intervention name.

    Handles combinations, normalizes names, and filters out non-drugs.

    Examples:
        "Cilostazol 100 MG" -> ["Cilostazol"]
        "Bevacizumab+Paclitaxel" -> ["Bevacizumab", "Paclitaxel"]
        "Adjuvant temozolomide 75 mg/m2" -> ["temozolomide"]
        "Placebo" -> []

    Args:
        raw_name: Raw intervention name from clinical trial

    Returns:
        List of normalized, queryable drug names
    """
    if not raw_name:
        return []

    # First normalize to remove dosage info
    normalized = normalize_drug_name(raw_name)

    # Check if it's a queryable drug
    if not should_query_external_apis(normalized):
        return []

    # Handle combinations
    if any(sep in normalized.lower() for sep in [' plus ', '+', ' and ']):
        # Split into components
        drugs = []
        for sep in [' plus ', '+', ' and ']:
            if sep in normalized.lower():
                drugs = re.split(re.escape(sep), normalized, flags=re.IGNORECASE)
                break

        # Clean each component
        result = []
        for drug in drugs:
            base = get_base_drug_name(drug.strip())
            if base and should_query_external_apis(base):
                result.append(base)
        return result
    else:
        # Single drug
        base = get_base_drug_name(normalized)
        if base and should_query_external_apis(base):
            return [base]
        return []


if __name__ == "__main__":
    # Test cases
    test_cases = [
        "Cilostazol 100 MG",
        "Minocycline 100mg",
        "Aspirin 81 mg",
        "VMD-928 300",
        "Paclitaxel 175 mg/m2",
        "Placebo",
        "Adjuvant temozolomide",
        "Bevacizumab plus Paclitaxel",
        "Cadonilimab+Bevacizumab+Pemetrexed+Carboplatin",
        "Gene modified anti-IL1RAP Chimeric Antigen Receptor T Cells :1.0×10^8",
    ]

    print("=== DRUG NAME NORMALIZATION TESTS ===\n")
    for name in test_cases:
        normalized = normalize_drug_name(name)
        base = get_base_drug_name(normalized)
        queryable = get_queryable_drug_names(name)

        print(f"Original:   {name}")
        print(f"Normalized: {normalized}")
        print(f"Base:       {base}")
        print(f"Queryable:  {queryable}")
        print()
