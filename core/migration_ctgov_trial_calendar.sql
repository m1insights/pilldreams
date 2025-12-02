-- Migration: CT.gov Trial Calendar + Query Tier System
-- Run this in Supabase SQL Editor
-- Date: 2025-12-02

-- ============================================================================
-- PART 1: Add query tier column to epi_drugs
-- ============================================================================

-- Add column to control CT.gov query strategy per drug
ALTER TABLE epi_drugs
ADD COLUMN IF NOT EXISTS ctgov_query_tier TEXT DEFAULT 'tier2_oncology';

-- Add constraint for valid values
ALTER TABLE epi_drugs
DROP CONSTRAINT IF EXISTS epi_drugs_ctgov_query_tier_check;

ALTER TABLE epi_drugs
ADD CONSTRAINT epi_drugs_ctgov_query_tier_check
CHECK (ctgov_query_tier IN ('tier1_curated', 'tier2_oncology', 'skip'));

COMMENT ON COLUMN epi_drugs.ctgov_query_tier IS
'CT.gov query strategy:
- tier1_curated: Only query specific NCT IDs from ci_curated_trials (for PCSK9, TTR, etc.)
- tier2_oncology: Query by drug name + oncology conditions filter (default for core epi drugs)
- skip: Do not query CT.gov for this drug';

-- Set Tier 1 for PCSK9 inhibitors (metabolic family - would return 200+ cardio trials)
UPDATE epi_drugs SET ctgov_query_tier = 'tier1_curated'
WHERE name IN (
    'ALIROCUMAB',
    'BOCOCIZUMAB',
    'EVOLOCUMAB',
    'FROVOCIMAB',
    'INCLISIRAN SODIUM',
    'LERODALCIBEP',
    'ONGERICIMAB',
    'RALPANCIZUMAB',
    'TAFOLECIMAB'
);

-- Set Tier 1 for TTR drugs (amyloidosis - not oncology)
UPDATE epi_drugs SET ctgov_query_tier = 'tier1_curated'
WHERE name IN (
    'ACORAMIDIS',
    'EPLONTERSEN',
    'INOTERSEN SODIUM',
    'PATISIRAN SODIUM',
    'REVUSIRAN',
    'TAFAMIDIS MEGLUMINE',
    'VUTRISIRAN SODIUM'
);

-- Set Tier 1 for E2F drugs (cell cycle, not classic epi)
UPDATE epi_drugs SET ctgov_query_tier = 'tier1_curated'
WHERE name IN (
    'EDIFOLIGIDE SODIUM'
);

-- Skip JQ1 (research tool, not in clinical trials)
UPDATE epi_drugs SET ctgov_query_tier = 'skip'
WHERE name = 'JQ1';

-- ============================================================================
-- PART 2: Curated trials table for Tier 1 drugs
-- ============================================================================

CREATE TABLE IF NOT EXISTS ci_curated_trials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Drug linkage
    drug_id UUID REFERENCES epi_drugs(id),
    drug_name TEXT NOT NULL,

    -- Trial identification
    nct_id TEXT NOT NULL UNIQUE,

    -- Why this trial is epigenetic-relevant
    relevance_notes TEXT,

    -- Metadata
    added_by TEXT DEFAULT 'manual',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_curated_trials_drug ON ci_curated_trials(drug_id);
CREATE INDEX IF NOT EXISTS idx_curated_trials_nct ON ci_curated_trials(nct_id);

COMMENT ON TABLE ci_curated_trials IS
'Manually curated NCT IDs for Tier 1 drugs (PCSK9, TTR, etc.) where automated
oncology filtering would return irrelevant trials. Only these specific trials
will be fetched from CT.gov for Tier 1 drugs.';

-- ============================================================================
-- PART 3: Main trial calendar table
-- ============================================================================

CREATE TABLE IF NOT EXISTS ci_trial_calendar (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Trial identification
    nct_id TEXT UNIQUE NOT NULL,
    trial_title TEXT,

    -- Key dates (the core value of this table)
    primary_completion_date DATE,
    primary_completion_type TEXT,  -- 'Actual' or 'Anticipated'
    study_completion_date DATE,
    study_completion_type TEXT,
    results_first_posted DATE,
    start_date DATE,

    -- Clinical classification
    phase TEXT,  -- 'Phase 1', 'Phase 2', 'Phase 3', 'Phase 4', 'Early Phase 1', 'Not Applicable'
    status TEXT,  -- 'Recruiting', 'Active, not recruiting', 'Completed', 'Terminated', 'Withdrawn', 'Suspended'

    -- Linkage to our entities
    drug_id UUID REFERENCES epi_drugs(id),
    drug_name TEXT,  -- Denormalized for quick display
    target_ids UUID[],
    indication_id UUID REFERENCES epi_indications(id),
    indication_name TEXT,  -- Denormalized

    -- Sponsor info
    lead_sponsor TEXT,
    lead_sponsor_type TEXT,  -- 'Industry', 'Academic', 'NIH', 'Other'
    collaborators TEXT[],

    -- Study design
    study_type TEXT,  -- 'Interventional', 'Observational'
    enrollment INTEGER,
    enrollment_type TEXT,  -- 'Actual' or 'Anticipated'

    -- Source tracking
    source TEXT DEFAULT 'clinicaltrials.gov',
    source_url TEXT,
    query_tier TEXT,  -- 'tier1_curated', 'tier2_oncology', 'tier3_discovery'

    -- Metadata
    last_api_update TIMESTAMPTZ,
    last_status_verified TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_trial_calendar_pcd ON ci_trial_calendar(primary_completion_date);
CREATE INDEX IF NOT EXISTS idx_trial_calendar_drug ON ci_trial_calendar(drug_id);
CREATE INDEX IF NOT EXISTS idx_trial_calendar_status ON ci_trial_calendar(status);
CREATE INDEX IF NOT EXISTS idx_trial_calendar_phase ON ci_trial_calendar(phase);
-- Note: Partial index with CURRENT_DATE not possible (not IMMUTABLE)
-- Use regular index instead - query optimizer will handle filtering
CREATE INDEX IF NOT EXISTS idx_trial_calendar_status_date ON ci_trial_calendar(status, primary_completion_date);

COMMENT ON TABLE ci_trial_calendar IS
'Clinical trial calendar for epigenetic oncology drugs. Contains trial dates,
phases, and status from ClinicalTrials.gov. Used for the Trial Readout Calendar
feature and alerts.';

-- ============================================================================
-- PART 4: Conference calendar (semi-static, seeded yearly)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ci_conferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Conference info
    name TEXT NOT NULL,  -- 'ASCO Annual Meeting'
    short_name TEXT,     -- 'ASCO'

    -- Dates
    start_date DATE NOT NULL,
    end_date DATE,
    abstract_deadline DATE,

    -- Details
    year INTEGER NOT NULL,
    location TEXT,
    url TEXT,

    -- Relevance
    oncology_focus BOOLEAN DEFAULT TRUE,
    epigenetics_track BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_conferences_unique ON ci_conferences(short_name, year);

COMMENT ON TABLE ci_conferences IS
'Major oncology conferences for the catalyst calendar. Seeded manually once
per year when conference dates are announced.';

-- Seed 2025 conferences
INSERT INTO ci_conferences (name, short_name, start_date, end_date, abstract_deadline, year, location, oncology_focus, epigenetics_track) VALUES
('ASCO Annual Meeting', 'ASCO', '2025-05-30', '2025-06-03', '2025-02-11', 2025, 'Chicago, IL', TRUE, FALSE),
('ASH Annual Meeting', 'ASH', '2025-12-06', '2025-12-09', '2025-08-05', 2025, 'San Diego, CA', TRUE, TRUE),
('AACR Annual Meeting', 'AACR', '2025-04-25', '2025-04-30', '2025-01-07', 2025, 'Chicago, IL', TRUE, TRUE),
('ESMO Congress', 'ESMO', '2025-09-12', '2025-09-16', '2025-05-15', 2025, 'Berlin, Germany', TRUE, FALSE),
('EHA Congress', 'EHA', '2025-06-12', '2025-06-15', '2025-02-20', 2025, 'Milan, Italy', TRUE, TRUE),
('SITC Annual Meeting', 'SITC', '2025-11-12', '2025-11-16', '2025-07-15', 2025, 'Houston, TX', TRUE, FALSE),
('World Conference on Lung Cancer', 'WCLC', '2025-09-06', '2025-09-09', '2025-04-15', 2025, 'Barcelona, Spain', TRUE, FALSE),
('San Antonio Breast Cancer Symposium', 'SABCS', '2025-12-09', '2025-12-13', '2025-09-01', 2025, 'San Antonio, TX', TRUE, FALSE)
ON CONFLICT (short_name, year) DO NOTHING;

-- ============================================================================
-- PART 5: Change log for tracking updates
-- ============================================================================

CREATE TABLE IF NOT EXISTS ci_change_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What changed
    entity_type TEXT NOT NULL,  -- 'drug', 'trial', 'company', 'patent', 'news'
    entity_id UUID,
    entity_name TEXT,

    -- Change details
    change_type TEXT NOT NULL,  -- 'phase_change', 'status_change', 'new_entity', 'score_change', 'date_change'
    field_changed TEXT,
    old_value TEXT,
    new_value TEXT,

    -- Significance for alerting
    significance TEXT DEFAULT 'low',  -- 'low', 'medium', 'high', 'critical'

    -- Source
    source TEXT,  -- 'ctgov', 'fda', 'news', 'patent', 'manual'
    source_url TEXT,

    -- Timestamps
    detected_at TIMESTAMPTZ DEFAULT NOW(),

    -- Digest status
    digest_sent BOOLEAN DEFAULT FALSE,
    digest_sent_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_change_log_entity ON ci_change_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_change_log_significance ON ci_change_log(significance);
CREATE INDEX IF NOT EXISTS idx_change_log_digest ON ci_change_log(digest_sent, detected_at);
CREATE INDEX IF NOT EXISTS idx_change_log_date ON ci_change_log(detected_at DESC);

COMMENT ON TABLE ci_change_log IS
'Audit trail of all changes detected across entities. Used for generating
weekly digests and triggering real-time alerts.';

-- ============================================================================
-- PART 6: Verify the migration
-- ============================================================================

-- Check Tier 1 drugs were set correctly
SELECT name, ctgov_query_tier
FROM epi_drugs
WHERE ctgov_query_tier != 'tier2_oncology'
ORDER BY ctgov_query_tier, name;

-- Count by tier
SELECT ctgov_query_tier, COUNT(*) as drug_count
FROM epi_drugs
GROUP BY ctgov_query_tier
ORDER BY ctgov_query_tier;
