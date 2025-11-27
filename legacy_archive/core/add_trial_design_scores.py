"""
Add design_quality_score column to trial table and score all existing trials.

This script:
1. Adds design_quality_score INT column to trial table (if not exists)
2. Fetches all trials in batches
3. Calculates design quality score for each trial
4. Updates database with scores
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.supabase_client import get_client
from core.trial_design_scorer import score_trial_design, get_quality_category
import structlog
from tqdm import tqdm

logger = structlog.get_logger()

BATCH_SIZE = 500  # Process 500 trials at a time


def add_column_if_not_exists():
    """Add design_quality_score column to trial table if it doesn't exist."""
    client = get_client()

    logger.info("Checking if design_quality_score column exists...")

    # Try to select the column - if it fails, we need to add it
    try:
        result = client.client.table('trial').select('design_quality_score').limit(1).execute()
        logger.info("Column design_quality_score already exists")
        return True
    except Exception as e:
        logger.info("Column design_quality_score does not exist, will need manual creation")
        logger.info("Please run this SQL in Supabase SQL Editor:")
        print("\n" + "="*80)
        print("RUN THIS SQL IN SUPABASE SQL EDITOR:")
        print("="*80)
        print("ALTER TABLE trial ADD COLUMN IF NOT EXISTS design_quality_score INT;")
        print("="*80 + "\n")
        return False


def score_all_trials():
    """Fetch all trials and calculate design quality scores."""
    client = get_client()

    logger.info("Fetching total trial count...")

    # Get total count
    count_result = client.client.table('trial').select('*', count='exact').limit(1).execute()
    total_trials = count_result.count

    logger.info(f"Total trials to score: {total_trials:,}")

    # Process in batches
    offset = 0
    scored_count = 0
    score_distribution = {"Excellent": 0, "Good": 0, "Fair": 0, "Poor": 0}

    with tqdm(total=total_trials, desc="Scoring trials") as pbar:
        while offset < total_trials:
            # Fetch batch
            trials = client.client.table('trial').select('*').range(offset, offset + BATCH_SIZE - 1).execute()

            if not trials.data:
                break

            # Score each trial in batch
            updates = []
            for trial in trials.data:
                score = score_trial_design(trial)
                category = get_quality_category(score)
                score_distribution[category] += 1

                updates.append({
                    'nct_id': trial['nct_id'],
                    'design_quality_score': score
                })

            # Batch update
            try:
                for update in updates:
                    client.client.table('trial').update({
                        'design_quality_score': update['design_quality_score']
                    }).eq('nct_id', update['nct_id']).execute()

                scored_count += len(updates)
                pbar.update(len(updates))

            except Exception as e:
                logger.error(f"Failed to update batch", error=str(e), offset=offset)
                # Continue with next batch

            offset += BATCH_SIZE

    logger.info(
        "Trial design scoring complete",
        total_scored=scored_count,
        distribution=score_distribution
    )

    print("\n" + "="*80)
    print("TRIAL DESIGN QUALITY SCORE DISTRIBUTION")
    print("="*80)
    for category, count in score_distribution.items():
        pct = (count / scored_count * 100) if scored_count > 0 else 0
        print(f"{category:12} {count:6,} trials ({pct:5.1f}%)")
    print("="*80 + "\n")

    return scored_count


if __name__ == "__main__":
    logger.info("Starting trial design scoring process...")

    # Step 1: Add column if needed
    column_exists = add_column_if_not_exists()

    if not column_exists:
        print("\n⚠️  Please add the design_quality_score column manually in Supabase SQL Editor.")
        print("After adding the column, run this script again.\n")
        sys.exit(1)

    # Step 2: Score all trials
    scored = score_all_trials()

    logger.info(f"✅ Successfully scored {scored:,} trials")
