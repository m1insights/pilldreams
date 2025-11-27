"""
Drug Scoring Algorithms

This module implements the scoring logic for pilldreams drug intelligence.
All scores are normalized to 0-100 scale.

Scoring Components:
1. Trial Progress Score (0-100) - Based on clinical trial advancement
2. Mechanism Score (0-100) - Based on target selectivity and validation
3. Safety Score (0-100) - Based on adverse event data
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from core.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class DrugScorer:
    """Main scoring engine for drug evaluation"""

    def __init__(self):
        self.client = SupabaseClient()
        self.supabase = self.client.client

    def calculate_all_scores(self, drug_id: str) -> Dict[str, float]:
        """
        Calculate all scores for a drug.

        Args:
            drug_id: UUID of the drug

        Returns:
            Dictionary with all scores:
            {
                'trial_progress_score': float,
                'mechanism_score': float,
                'safety_score': float,
                'overall_score': float
            }
        """
        try:
            trial_score = self.calculate_trial_progress_score(drug_id)
            mechanism_score = self.calculate_mechanism_score(drug_id)
            safety_score = self.calculate_safety_score(drug_id)

            # Overall score is weighted average
            overall_score = (
                trial_score * 0.4 +
                mechanism_score * 0.3 +
                safety_score * 0.3
            )

            return {
                'trial_progress_score': round(trial_score, 1),
                'mechanism_score': round(mechanism_score, 1),
                'safety_score': round(safety_score, 1),
                'overall_score': round(overall_score, 1)
            }
        except Exception as e:
            logger.error(f"Error calculating scores for drug {drug_id}: {e}")
            return {
                'trial_progress_score': 0.0,
                'mechanism_score': 0.0,
                'safety_score': 0.0,
                'overall_score': 0.0
            }

    def calculate_trial_progress_score(self, drug_id: str) -> float:
        """
        Calculate Trial Progress Score (0-100).

        Factors:
        - Highest phase reached (0-40 points)
        - Trial completion rate (0-20 points)
        - Sponsor quality (0-15 points)
        - Trial design quality (0-15 points)
        - Enrollment size (0-10 points)

        Args:
            drug_id: UUID of the drug

        Returns:
            Score from 0-100
        """
        try:
            # Get all trials for this drug
            response = self.supabase.table('trial').select('*').eq('drug_id', drug_id).execute()
            trials = response.data

            if not trials:
                return 0.0

            # 1. Highest phase reached (0-40 points)
            phase_map = {'0': 5, 'I': 10, 'I/II': 15, 'II': 20, 'II/III': 25, 'III': 35, 'IV': 40}
            highest_phase_score = 0.0

            for trial in trials:
                phase = trial.get('phase', '')
                if phase in phase_map:
                    highest_phase_score = max(highest_phase_score, phase_map[phase])

            # 2. Trial completion rate (0-20 points)
            completed_trials = [t for t in trials if t.get('status') == 'Completed']
            terminated_trials = [t for t in trials if t.get('status') in ['Terminated', 'Withdrawn', 'Suspended']]

            total_finished = len(completed_trials) + len(terminated_trials)
            if total_finished > 0:
                completion_rate = len(completed_trials) / total_finished
                completion_score = completion_rate * 20
            else:
                completion_score = 10.0  # Neutral score if no finished trials

            # 3. Sponsor quality (0-15 points)
            industry_trials = [t for t in trials if t.get('sponsor_type') == 'Industry']
            if len(trials) > 0:
                industry_ratio = len(industry_trials) / len(trials)
                sponsor_score = industry_ratio * 15
            else:
                sponsor_score = 0.0

            # 4. Trial design quality (0-15 points)
            design_scores = [t.get('design_quality_score', 0) for t in trials if t.get('design_quality_score')]
            if design_scores:
                avg_design_score = sum(design_scores) / len(design_scores)
                # design_quality_score is already 0-100, normalize to 0-15
                design_score = (avg_design_score / 100) * 15
            else:
                design_score = 7.5  # Neutral score

            # 5. Enrollment size (0-10 points)
            enrollments = [t.get('enrollment', 0) for t in trials if t.get('enrollment')]
            if enrollments:
                max_enrollment = max(enrollments)
                # Score based on logarithmic scale
                # 100 patients = 5 pts, 1000 = 8 pts, 10000+ = 10 pts
                if max_enrollment >= 10000:
                    enrollment_score = 10.0
                elif max_enrollment >= 1000:
                    enrollment_score = 8.0
                elif max_enrollment >= 100:
                    enrollment_score = 5.0
                else:
                    enrollment_score = 2.0
            else:
                enrollment_score = 0.0

            total_score = (
                highest_phase_score +
                completion_score +
                sponsor_score +
                design_score +
                enrollment_score
            )

            return min(total_score, 100.0)

        except Exception as e:
            logger.error(f"Error calculating trial progress score: {e}")
            return 0.0

    def calculate_mechanism_score(self, drug_id: str) -> float:
        """
        Calculate Mechanism Score (0-100).

        Factors:
        - Target validation (0-30 points)
        - Selectivity (0-30 points)
        - Binding affinity (0-25 points)
        - Target count (0-15 points)

        Args:
            drug_id: UUID of the drug

        Returns:
            Score from 0-100
        """
        try:
            # Get drug-target bindings
            response = self.supabase.table('drugtarget') \
                .select('*, target(*)') \
                .eq('drug_id', drug_id) \
                .execute()
            bindings = response.data

            if not bindings:
                return 0.0

            # 1. Target validation score (0-30 points)
            # Higher score if targets are well-known drug targets
            validated_targets = ['CHEMBL1862', 'CHEMBL204', 'CHEMBL233', 'CHEMBL240']  # Example: known validated targets
            target_ids = [b.get('target_id') for b in bindings]

            # For now, give points based on having any targets (simplified)
            if len(target_ids) > 0:
                validation_score = 20.0  # Base score for having characterized targets
            else:
                validation_score = 0.0

            # 2. Selectivity score (0-30 points)
            # Penalize drugs that hit too many targets (off-target effects)
            num_targets = len(bindings)
            if num_targets == 1:
                selectivity_score = 30.0  # Highly selective
            elif num_targets <= 3:
                selectivity_score = 25.0  # Good selectivity
            elif num_targets <= 5:
                selectivity_score = 20.0  # Moderate selectivity
            elif num_targets <= 10:
                selectivity_score = 15.0  # Poor selectivity
            else:
                selectivity_score = 10.0  # Very promiscuous

            # 3. Binding affinity score (0-25 points)
            # Lower IC50/Ki = better affinity
            affinities = []
            for binding in bindings:
                affinity_value = binding.get('affinity_value')
                affinity_type = binding.get('affinity_type')

                if affinity_value and affinity_type in ['IC50', 'Ki', 'Kd']:
                    affinities.append(affinity_value)

            if affinities:
                best_affinity = min(affinities)  # Lower is better (nM scale)

                # Score based on affinity strength
                if best_affinity < 1:  # Sub-nanomolar
                    affinity_score = 25.0
                elif best_affinity < 10:  # Single-digit nM
                    affinity_score = 22.0
                elif best_affinity < 100:  # Double-digit nM
                    affinity_score = 18.0
                elif best_affinity < 1000:  # Triple-digit nM
                    affinity_score = 14.0
                else:  # Micromolar range
                    affinity_score = 10.0
            else:
                affinity_score = 12.5  # Neutral score if no affinity data

            # 4. Target count bonus (0-15 points)
            # Reward having multiple characterized interactions (up to a point)
            measurement_counts = [b.get('measurement_count', 0) for b in bindings]
            total_measurements = sum(measurement_counts)

            if total_measurements >= 50:
                measurement_score = 15.0
            elif total_measurements >= 20:
                measurement_score = 12.0
            elif total_measurements >= 10:
                measurement_score = 9.0
            elif total_measurements >= 5:
                measurement_score = 6.0
            else:
                measurement_score = 3.0

            total_score = (
                validation_score +
                selectivity_score +
                affinity_score +
                measurement_score
            )

            return min(total_score, 100.0)

        except Exception as e:
            logger.error(f"Error calculating mechanism score: {e}")
            return 0.0

    def calculate_safety_score(self, drug_id: str) -> float:
        """
        Calculate Safety Score (0-100).

        Higher score = better safety profile

        Factors:
        - Serious adverse events (0-40 points penalty)
        - Total adverse event count (0-30 points penalty)
        - Disproportionality signals (0-30 points penalty)

        Args:
            drug_id: UUID of the drug

        Returns:
            Score from 0-100 (100 = best safety)
        """
        try:
            # Get safety data
            response = self.supabase.table('safetyaggregate') \
                .select('*') \
                .eq('drug_id', drug_id) \
                .execute()
            safety_events = response.data

            if not safety_events:
                # No safety data = neutral score (not necessarily safe, just unknown)
                return 70.0

            # Start with perfect score and deduct points
            score = 100.0

            # 1. Serious adverse events penalty (0-40 points)
            serious_events = [e for e in safety_events if e.get('is_serious')]
            total_serious_cases = sum(e.get('case_count', 0) for e in serious_events)

            if total_serious_cases >= 1000:
                score -= 40.0
            elif total_serious_cases >= 500:
                score -= 30.0
            elif total_serious_cases >= 100:
                score -= 20.0
            elif total_serious_cases >= 50:
                score -= 10.0
            elif total_serious_cases > 0:
                score -= 5.0

            # 2. Total adverse event count penalty (0-30 points)
            total_cases = sum(e.get('case_count', 0) for e in safety_events)

            if total_cases >= 10000:
                score -= 30.0
            elif total_cases >= 5000:
                score -= 25.0
            elif total_cases >= 1000:
                score -= 20.0
            elif total_cases >= 500:
                score -= 15.0
            elif total_cases >= 100:
                score -= 10.0

            # 3. Disproportionality signals penalty (0-30 points)
            # High disproportionality metric suggests stronger association than expected
            high_signal_events = [
                e for e in safety_events
                if e.get('disproportionality_metric', 0) > 2.0
            ]

            if len(high_signal_events) >= 10:
                score -= 30.0
            elif len(high_signal_events) >= 5:
                score -= 20.0
            elif len(high_signal_events) >= 3:
                score -= 15.0
            elif len(high_signal_events) >= 1:
                score -= 10.0

            return max(score, 0.0)

        except Exception as e:
            logger.error(f"Error calculating safety score: {e}")
            return 70.0  # Neutral score on error


def calculate_scores_for_drug(drug_id: str) -> Dict[str, float]:
    """
    Convenience function to calculate all scores for a drug.

    Args:
        drug_id: UUID of the drug

    Returns:
        Dictionary with all scores
    """
    scorer = DrugScorer()
    return scorer.calculate_all_scores(drug_id)


def calculate_scores_batch(drug_ids: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Calculate scores for multiple drugs in batch.

    Args:
        drug_ids: List of drug UUIDs

    Returns:
        Dictionary mapping drug_id to scores dict
    """
    scorer = DrugScorer()
    results = {}

    for drug_id in drug_ids:
        results[drug_id] = scorer.calculate_all_scores(drug_id)

    return results
