"""
Trial Design Quality Scorer

Scores each clinical trial on design quality (0-100) based on:
- Randomization
- Blinding
- Control groups (placebo, active comparator)
- Endpoint quality
- Multi-center status
- Enrollment tracking

Higher scores indicate more robust trial designs.
"""

import structlog
from typing import Dict, Any
from datetime import datetime

logger = structlog.get_logger()


def score_trial_design(trial: Dict[str, Any]) -> int:
    """
    Calculate trial design quality score (0-100).

    Args:
        trial: Dictionary with trial data from Supabase

    Returns:
        Integer score 0-100

    Scoring breakdown:
    - Randomization: +20 points
    - Blinding: +20 (double-blind), +10 (single-blind)
    - Placebo arm: +15 points
    - Active comparator: +15 points
    - Endpoint quality: +15 (OS/PFS), +5 (surrogate)
    - Multi-center: +10 points
    - Enrollment on track: +5 points
    """
    score = 0

    # 1. Randomization (+20)
    if trial.get('is_randomized'):
        score += 20
        logger.debug("Randomized trial", nct_id=trial.get('nct_id'), points=20)

    # 2. Blinding (+20 double, +10 single)
    is_blinded = trial.get('is_blinded')
    if is_blinded:
        # Assume double-blind if blinded (can't distinguish from current data)
        score += 20
        logger.debug("Blinded trial", nct_id=trial.get('nct_id'), points=20)

    # 3. Placebo arm (+15)
    if trial.get('has_placebo_arm'):
        score += 15
        logger.debug("Placebo-controlled", nct_id=trial.get('nct_id'), points=15)

    # 4. Active comparator (+15)
    if trial.get('has_active_comparator'):
        score += 15
        logger.debug("Active comparator", nct_id=trial.get('nct_id'), points=15)

    # 5. Endpoint quality (+15 for OS/PFS, +5 for surrogate)
    endpoint = trial.get('primary_endpoint', '').lower()

    # Gold standard endpoints
    if any(term in endpoint for term in ['overall survival', 'os ', 'progression-free survival', 'pfs', 'event-free survival']):
        score += 15
        logger.debug("Gold standard endpoint", nct_id=trial.get('nct_id'), endpoint_type="OS/PFS", points=15)
    # Surrogate endpoints
    elif any(term in endpoint for term in ['response rate', 'tumor size', 'objective response', 'complete response', 'biomarker']):
        score += 5
        logger.debug("Surrogate endpoint", nct_id=trial.get('nct_id'), endpoint_type="surrogate", points=5)
    # Other clinical endpoints (partial credit)
    elif endpoint and endpoint != 'not available':
        score += 10
        logger.debug("Clinical endpoint", nct_id=trial.get('nct_id'), points=10)

    # 6. Multi-center (+10)
    # Note: We don't currently have location count in our schema
    # This would require additional data from ClinicalTrials.gov
    # For now, we'll skip this criterion or assume single-center

    # 7. Enrollment on track (+5)
    # Check if enrollment is progressing appropriately
    status = trial.get('status', '')
    enrollment = trial.get('enrollment', 0)

    if status in ['Active, not recruiting', 'Completed'] and enrollment > 50:
        # Trial reached significant enrollment
        score += 5
        logger.debug("Adequate enrollment", nct_id=trial.get('nct_id'), enrollment=enrollment, points=5)
    elif status == 'Recruiting' and enrollment > 100:
        # Large ongoing trial
        score += 3
        logger.debug("Large ongoing trial", nct_id=trial.get('nct_id'), enrollment=enrollment, points=3)

    # Cap at 100
    final_score = min(score, 100)

    logger.info(
        "Trial design scored",
        nct_id=trial.get('nct_id'),
        score=final_score,
        randomized=trial.get('is_randomized'),
        blinded=trial.get('is_blinded'),
        placebo=trial.get('has_placebo_arm'),
        comparator=trial.get('has_active_comparator')
    )

    return final_score


def get_quality_category(score: int) -> str:
    """
    Categorize trial design quality based on score.

    Args:
        score: Trial design quality score (0-100)

    Returns:
        Category string: Excellent, Good, Fair, or Poor
    """
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Fair"
    else:
        return "Poor"


def explain_score(trial: Dict[str, Any], score: int) -> str:
    """
    Generate human-readable explanation of trial design score.

    Args:
        trial: Dictionary with trial data
        score: Calculated design quality score

    Returns:
        Explanation string
    """
    category = get_quality_category(score)

    strengths = []
    weaknesses = []

    if trial.get('is_randomized'):
        strengths.append("randomized")
    else:
        weaknesses.append("not randomized")

    if trial.get('is_blinded'):
        strengths.append("blinded")
    else:
        weaknesses.append("not blinded")

    if trial.get('has_placebo_arm'):
        strengths.append("placebo-controlled")

    if trial.get('has_active_comparator'):
        strengths.append("active comparator")

    endpoint = trial.get('primary_endpoint', '').lower()
    if any(term in endpoint for term in ['overall survival', 'progression-free']):
        strengths.append("gold standard endpoint (OS/PFS)")
    elif any(term in endpoint for term in ['response rate', 'tumor size']):
        weaknesses.append("surrogate endpoint")

    strength_str = ", ".join(strengths) if strengths else "none identified"
    weakness_str = ", ".join(weaknesses) if weaknesses else "none identified"

    explanation = f"Trial Design Quality: {category} ({score}/100)\n"
    explanation += f"Strengths: {strength_str}\n"
    explanation += f"Areas for improvement: {weakness_str}"

    return explanation


if __name__ == "__main__":
    # Test with sample trial data
    sample_trial = {
        'nct_id': 'NCT00000001',
        'is_randomized': True,
        'is_blinded': True,
        'has_placebo_arm': True,
        'has_active_comparator': False,
        'primary_endpoint': 'Overall Survival',
        'enrollment': 500,
        'status': 'Completed'
    }

    score = score_trial_design(sample_trial)
    explanation = explain_score(sample_trial, score)

    print(f"\nTest Trial Score: {score}/100")
    print(f"Category: {get_quality_category(score)}")
    print(f"\n{explanation}")
