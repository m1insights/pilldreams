-- ============================================================================
-- MIGRATION: Per-Target Activity Breakdown
-- ============================================================================
-- Stores ChEMBL activity data broken down by target for potency visualization
-- Run in Supabase Dashboard > SQL Editor
-- ============================================================================

CREATE TABLE IF NOT EXISTS chembl_target_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drug_id UUID NOT NULL REFERENCES epi_drugs(id) ON DELETE CASCADE,

    -- Target info from ChEMBL
    target_chembl_id TEXT,           -- e.g., CHEMBL2007625
    target_name TEXT NOT NULL,       -- e.g., "Isocitrate dehydrogenase [NADP] cytoplasmic"
    target_type TEXT,                -- e.g., "SINGLE PROTEIN", "CELL-LINE"

    -- Potency metrics
    best_pact REAL,                  -- Best pXC50 (highest potency)
    median_pact REAL,                -- Median pXC50
    best_value_nm REAL,              -- Best IC50/Ki in nM (for display)

    -- Activity counts
    n_activities INTEGER DEFAULT 0,  -- Number of measurements
    activity_types TEXT[],           -- Array of types: {"IC50", "Ki", "Kd"}

    -- Metadata
    is_primary_target BOOLEAN DEFAULT FALSE,  -- Is this the drug's main target?
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint: one row per drug-target pair
    UNIQUE(drug_id, target_chembl_id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_target_activities_drug ON chembl_target_activities(drug_id);
CREATE INDEX IF NOT EXISTS idx_target_activities_best_pact ON chembl_target_activities(best_pact DESC);

-- Comments
COMMENT ON TABLE chembl_target_activities IS 'Per-target ChEMBL activity breakdown for potency visualization';
COMMENT ON COLUMN chembl_target_activities.best_pact IS 'Best pXC50 = 9 - log10(nM). Higher = more potent';
COMMENT ON COLUMN chembl_target_activities.best_value_nm IS 'Best IC50/Ki in nanomolar for human-readable display';
