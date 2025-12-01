import requests
import math
import statistics
from typing import Dict, List, Optional

CHEMBL_API_URL = "https://www.ebi.ac.uk/chembl/api/data"

def fetch_chembl_activity(chembl_molecule_id: str, target_chembl_id: Optional[str] = None) -> Dict:
    """
    Fetch bioactivity data from ChEMBL for a given molecule.
    Returns metrics: p_act_median, p_act_best, p_off_best, delta_p, n_primary, n_total.
    """
    # 1. Fetch all valid activities for the molecule
    # Filter: Standard units nM, Types Ki/Kd/IC50/EC50, Confidence >= 7 (if possible via API or post-filter)
    # API allows filtering by molecule_chembl_id and standard_type.
    # We will fetch all relevant types and filter in Python for flexibility.
    
    url = f"{CHEMBL_API_URL}/activity"
    params = {
        "molecule_chembl_id": chembl_molecule_id,
        "standard_type__in": "Ki,Kd,IC50,EC50",
        "standard_units": "nM",
        "limit": 1000, # Fetch reasonable amount
        "format": "json"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        activities = data.get("activities", [])
    except Exception as e:
        print(f"❌ Error fetching ChEMBL activities for {chembl_molecule_id}: {e}")
        return {}

    primary_p_values = []
    off_target_p_values = []
    
    n_primary = 0
    n_total = 0

    for act in activities:
        # Quality Filters
        # Assay type: 'B' (Binding) or 'F' (Functional) usually preferred.
        # ChEMBL API returns `assay_type`.
        if act.get("assay_type") not in ["B", "F"]:
            continue
            
        # Confidence Score (if available, usually mapped to `data_validity_comment` or similar in older versions, 
        # but modern ChEMBL has `confidence_score` in some endpoints. 
        # Let's check if `confidence_score` is present. If not, we skip strict check or rely on `standard_value`.
        # Actually, `standard_value` must be present.
        val = act.get("standard_value")
        if not val:
            continue
            
        try:
            val_nm = float(val)
        except:
            continue
            
        # Calculate pXC50
        # pXC50 = 9 - log10(nM)
        if val_nm <= 0: continue
        p_val = 9 - math.log10(val_nm)
        
        n_total += 1
        
        # Check if Primary or Off-Target
        # We need the target_chembl_id of the activity
        act_target_id = act.get("target_chembl_id")

        if target_chembl_id is None:
            # No specific target provided - use ALL activities for "best potency"
            # This gives us the drug's overall best potency across all targets
            primary_p_values.append(p_val)
            n_primary += 1
        elif act_target_id == target_chembl_id:
            primary_p_values.append(p_val)
            n_primary += 1
        else:
            off_target_p_values.append(p_val)

    # Compute Metrics
    metrics = {
        "n_activities_primary": n_primary,
        "n_activities_total": n_total,
        "p_act_median": None,
        "p_act_best": None,
        "p_off_best": None,
        "delta_p": None
    }
    
    if primary_p_values:
        metrics["p_act_median"] = statistics.median(primary_p_values)
        metrics["p_act_best"] = max(primary_p_values)
        
    if off_target_p_values:
        metrics["p_off_best"] = max(off_target_p_values)
        
    if metrics["p_act_best"] is not None and metrics["p_off_best"] is not None:
        metrics["delta_p"] = metrics["p_act_best"] - metrics["p_off_best"]
    elif metrics["p_act_best"] is not None:
        # If no off-target data, we can't strictly calculate delta_p.
        # But maybe we assume it's good? Or None.
        pass
        
    return metrics
