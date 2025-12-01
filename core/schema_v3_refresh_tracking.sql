-- Schema v3: Add refresh tracking for ongoing maintenance
-- Tracks when we last queried external APIs (Open Targets, ChEMBL) for each entity

-- Add refresh tracking to epi_targets
ALTER TABLE epi_targets
ADD COLUMN IF NOT EXISTS last_ot_refresh TIMESTAMPTZ NULL,
ADD COLUMN IF NOT EXISTS last_chembl_refresh TIMESTAMPTZ NULL;

COMMENT ON COLUMN epi_targets.last_ot_refresh IS 'When we last queried Open Targets for this target';
COMMENT ON COLUMN epi_targets.last_chembl_refresh IS 'When we last queried ChEMBL for this target';

-- Add refresh tracking to epi_drugs
ALTER TABLE epi_drugs
ADD COLUMN IF NOT EXISTS last_ot_refresh TIMESTAMPTZ NULL,
ADD COLUMN IF NOT EXISTS last_chembl_refresh TIMESTAMPTZ NULL;

COMMENT ON COLUMN epi_drugs.last_ot_refresh IS 'When we last queried Open Targets for this drug';
COMMENT ON COLUMN epi_drugs.last_chembl_refresh IS 'When we last queried ChEMBL for this drug';

-- Add refresh tracking to epi_indications
ALTER TABLE epi_indications
ADD COLUMN IF NOT EXISTS last_ot_refresh TIMESTAMPTZ NULL;

COMMENT ON COLUMN epi_indications.last_ot_refresh IS 'When we last queried Open Targets for this indication';

-- Create a refresh log table for audit trail
CREATE TABLE IF NOT EXISTS etl_refresh_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL,  -- 'target', 'drug', 'indication'
    entity_id UUID NOT NULL,
    api_source TEXT NOT NULL,   -- 'open_targets', 'chembl', 'clinicaltrials'
    refresh_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    records_found INTEGER DEFAULT 0,
    status TEXT DEFAULT 'success',  -- 'success', 'error', 'no_data'
    error_message TEXT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_refresh_log_entity ON etl_refresh_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_refresh_log_date ON etl_refresh_log(refresh_date DESC);

COMMENT ON TABLE etl_refresh_log IS 'Audit trail of API refreshes for data freshness tracking';
