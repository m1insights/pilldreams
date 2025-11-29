"""
12_compute_editing_scores.py

Computes EditingScore for each editing asset.

Formula: EditingScore = 0.5 * TargetBioScore + 0.3 * EditingModalityScore + 0.2 * DurabilityScore

Components:
1. Target Biology Score (50%): Open Targets association scores for target-indication pair
2. Editing Modality Score (30%): Based on delivery type, effector domains, platform maturity
3. Durability Score (20%): Assessment of epigenetic mark stability vs reversibility

Run: python -m backend.etl.12_compute_editing_scores
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from backend.etl import supabase_client, open_targets


# Modality scoring parameters
DELIVERY_SCORES = {
    "LNP_mRNA": 85,      # High delivery efficiency, proven clinical use
    "AAV": 75,           # Good for CNS/muscle, but immunogenicity concerns
    "Nanoparticle": 70,  # Various formulations
    "other": 50,
}

DBD_SCORES = {
    "CRISPR_dCas9": 90,  # Most versatile, well-characterized
    "CRISPR_dSaCas9": 85,  # Smaller, good for AAV
    "ZF": 80,            # Proven technology, no PAM requirement
    "TALE": 75,          # Larger, less common
    "Base_Editor": 70,   # Different mechanism (DNA editing vs epi)
    "other": 50,
}

EFFECTOR_SCORES = {
    "combo": 95,         # KRAB+DNMT3A/3L = durable silencing
    "writer": 85,        # DNMT3A/3L alone
    "indirect_repressor": 75,  # KRAB alone (transient)
    "eraser": 70,        # TET1 (reactivation)
    "indirect_activator": 65,  # VPR, VP64 (transient)
    "other": 50,
}

# Phase-based maturity bonus
PHASE_MATURITY = {
    0: 0,   # Preclinical
    1: 15,  # Phase 1
    2: 30,  # Phase 2
    3: 45,  # Phase 3
    4: 50,  # Approved
}


def run():
    print("=" * 60)
    print("12_compute_editing_scores.py")
    print("Computing EditingScores for all assets")
    print("=" * 60)

    assets = supabase_client.get_all_editing_assets()
    print(f"Found {len(assets)} editing assets.\n")

    for asset in assets:
        name = asset["name"]
        print(f"Scoring: {name}")

        # 1. Target Biology Score
        target_bio_score = _compute_target_bio_score(asset)
        print(f"  Target Bio Score: {target_bio_score:.1f}")

        # 2. Editing Modality Score
        modality_score = _compute_modality_score(asset)
        print(f"  Modality Score: {modality_score:.1f}")

        # 3. Durability Score
        durability_score = _compute_durability_score(asset)
        print(f"  Durability Score: {durability_score:.1f}")

        # Total weighted score
        total_score = (
            0.5 * target_bio_score +
            0.3 * modality_score +
            0.2 * durability_score
        )
        print(f"  TOTAL EDITING SCORE: {total_score:.1f}")

        # Build rationale
        rationale = _build_rationale(asset, target_bio_score, modality_score, durability_score)

        # Save scores
        score_data = {
            "editing_asset_id": asset["id"],
            "target_bio_score": round(target_bio_score, 2),
            "editing_modality_score": round(modality_score, 2),
            "durability_score": round(durability_score, 2),
            "total_editing_score": round(total_score, 2),
            "score_rationale": rationale,
        }

        try:
            supabase_client.upsert_editing_scores(score_data)
            print(f"  Saved scores for {name}\n")
        except Exception as e:
            print(f"  ERROR saving scores: {e}\n")

    print("=" * 60)
    print("DONE: EditingScores computed for all assets")
    print("=" * 60)


def _compute_target_bio_score(asset: dict) -> float:
    """
    Compute target biology score based on Open Targets disease association.
    Range: 0-100
    """
    target_symbol = asset.get("target_gene_symbol")
    indication = asset.get("primary_indication")

    if not target_symbol:
        return 30.0  # Baseline for unknown targets

    # Skip non-gene targets (viruses, etc.)
    if target_symbol in ["HBV", "HCV", "HIV", "Various"]:
        # For viral targets, assume high biological validity
        return 75.0

    # Try to get Open Targets association score
    try:
        ot_target = open_targets.search_target_by_symbol(target_symbol)
        if not ot_target:
            return 40.0

        ot_id = ot_target["id"]

        # Fetch disease associations
        associations = open_targets.fetch_target_disease_associations(ot_id)
        if not associations:
            return 45.0

        # Find the best association score for this indication
        best_score = 0.0
        indication_lower = indication.lower() if indication else ""

        for assoc in associations[:50]:  # Check top 50 associations
            disease_name = assoc.get("disease", {}).get("name", "").lower()
            score = assoc.get("score", 0)

            # Check for indication match
            if indication_lower:
                if indication_lower in disease_name or disease_name in indication_lower:
                    return min(score * 100, 100)

            if score > best_score:
                best_score = score

        # Return best score normalized to 0-100, with a floor
        return max(best_score * 100, 40.0)

    except Exception as e:
        print(f"    WARN: Could not compute bio score for {target_symbol}: {e}")
        return 40.0


def _compute_modality_score(asset: dict) -> float:
    """
    Compute modality score based on delivery, DBD type, effectors, and maturity.
    Range: 0-100
    """
    delivery_type = asset.get("delivery_type", "other")
    dbd_type = asset.get("dbd_type", "other")
    effector_type = asset.get("effector_type", "other")
    phase = asset.get("phase", 0)

    # Base scores
    delivery_score = DELIVERY_SCORES.get(delivery_type, DELIVERY_SCORES["other"])
    dbd_score = DBD_SCORES.get(dbd_type, DBD_SCORES["other"])
    effector_score = EFFECTOR_SCORES.get(effector_type, EFFECTOR_SCORES["other"])
    maturity_bonus = PHASE_MATURITY.get(phase, 0)

    # Weighted combination (delivery 30%, DBD 30%, effector 30%, maturity 10%)
    base_score = (
        0.30 * delivery_score +
        0.30 * dbd_score +
        0.30 * effector_score +
        0.10 * (50 + maturity_bonus)  # Maturity starts at 50, +bonus
    )

    return min(base_score, 100)


def _compute_durability_score(asset: dict) -> float:
    """
    Compute durability score based on epigenetic mechanism.

    Key factors:
    - DNA methylation (DNMT3A/3L) = most durable
    - Combo (KRAB + DNMT) = very durable
    - KRAB alone = transient (weeks)
    - Activators (VP64, VPR) = transient

    Range: 0-100
    """
    effector_type = asset.get("effector_type", "other")
    effector_domains = asset.get("effector_domains", []) or []

    # Check for DNMT presence (durable methylation)
    has_dnmt = any("DNMT" in d.upper() for d in effector_domains)
    has_krab = any("KRAB" in d.upper() for d in effector_domains)
    has_activator = any(d.upper() in ["VP64", "VPR", "P65", "RTA"] for d in effector_domains)
    has_eraser = any("TET" in d.upper() for d in effector_domains)

    # Score based on durability profile
    if has_dnmt and has_krab:
        # Combo = most durable (CRISPRoff-like)
        return 95.0
    elif has_dnmt:
        # DNMT alone = very durable
        return 85.0
    elif effector_type == "combo":
        # Some combo without DNMT
        return 80.0
    elif has_krab:
        # KRAB alone = weeks to months
        return 65.0
    elif has_eraser:
        # TET = gene reactivation, useful but different
        return 60.0
    elif has_activator:
        # Activators = transient
        return 50.0
    else:
        return 50.0


def _build_rationale(asset: dict, bio_score: float, modality_score: float, durability_score: float) -> str:
    """Build a brief rationale for the scoring."""
    parts = []

    # Target biology
    target = asset.get("target_gene_symbol", "Unknown")
    indication = asset.get("primary_indication", "Unknown indication")
    parts.append(f"Target: {target} for {indication}")

    # Modality highlights
    delivery = asset.get("delivery_type", "Unknown")
    dbd = asset.get("dbd_type", "Unknown")
    parts.append(f"Platform: {dbd} via {delivery}")

    # Durability assessment
    effector_type = asset.get("effector_type", "unknown")
    if effector_type == "combo":
        parts.append("Durability: High (combo effector)")
    elif "DNMT" in str(asset.get("effector_domains", [])).upper():
        parts.append("Durability: High (DNA methylation)")
    elif effector_type == "indirect_repressor":
        parts.append("Durability: Moderate (indirect repressor)")
    else:
        parts.append(f"Durability: {effector_type}")

    # Phase
    phase = asset.get("phase", 0)
    status = asset.get("status", "unknown")
    if phase >= 1:
        parts.append(f"Stage: Phase {phase} ({status})")
    else:
        parts.append(f"Stage: Preclinical ({status})")

    return ". ".join(parts)


if __name__ == "__main__":
    run()
