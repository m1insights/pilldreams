-- Migration: Add trial_intervention junction table
-- Purpose: Fix many-to-many relationship between trials and drugs
-- Date: 2025-11-22

-- Step 1: Create junction table
CREATE TABLE IF NOT EXISTS trial_intervention (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  trial_id VARCHAR(50) REFERENCES trial(nct_id) ON DELETE CASCADE,
  drug_id UUID REFERENCES drug(id) ON DELETE CASCADE,
  intervention_role VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(trial_id, drug_id)
);

CREATE INDEX IF NOT EXISTS idx_trial_intervention_trial ON trial_intervention(trial_id);
CREATE INDEX IF NOT EXISTS idx_trial_intervention_drug ON trial_intervention(drug_id);

-- Step 2: Migrate existing trial -> drug links to junction table
INSERT INTO trial_intervention (trial_id, drug_id, intervention_role)
SELECT nct_id, drug_id, 'experimental'
FROM trial
WHERE drug_id IS NOT NULL
ON CONFLICT (trial_id, drug_id) DO NOTHING;

-- Step 3: Remove drug_id from trial table (we'll keep it for now for backwards compatibility)
-- LATER: ALTER TABLE trial DROP COLUMN drug_id;

COMMENT ON TABLE trial_intervention IS 'Many-to-many relationship between trials and drugs (interventions)';
COMMENT ON COLUMN trial_intervention.intervention_role IS 'Role of drug in trial: experimental, comparator, placebo, etc.';
