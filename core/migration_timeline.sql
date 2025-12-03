-- Historical Timeline Tables
-- Tracks when drugs/companies entered phases or had status changes

-- ============================================
-- Drug Phase History
-- ============================================
CREATE TABLE IF NOT EXISTS epi_drug_phase_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    drug_id UUID NOT NULL REFERENCES epi_drugs(id) ON DELETE CASCADE,
    drug_name TEXT NOT NULL,  -- Denormalized for query efficiency

    -- Phase data
    phase_from INTEGER,  -- NULL if first record
    phase_to INTEGER NOT NULL,

    -- Approval data
    fda_approved_from BOOLEAN DEFAULT FALSE,
    fda_approved_to BOOLEAN DEFAULT FALSE,

    -- Context
    indication_id UUID REFERENCES epi_indications(id),
    indication_name TEXT,  -- Denormalized

    -- Source information
    source TEXT,  -- 'etl', 'manual', 'clinicaltrials', 'fda'
    source_url TEXT,
    notes TEXT,

    -- Timestamps
    change_date DATE NOT NULL,  -- When the change occurred
    detected_at TIMESTAMPTZ DEFAULT NOW(),  -- When we detected it
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- For efficient querying
    CONSTRAINT valid_phase CHECK (phase_to >= 0 AND phase_to <= 4)
);

CREATE INDEX idx_drug_phase_history_drug ON epi_drug_phase_history(drug_id);
CREATE INDEX idx_drug_phase_history_date ON epi_drug_phase_history(change_date DESC);
CREATE INDEX idx_drug_phase_history_phase ON epi_drug_phase_history(phase_to);

-- ============================================
-- Company Entry History (when company entered epi space)
-- ============================================
CREATE TABLE IF NOT EXISTS epi_company_entry_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_id UUID NOT NULL REFERENCES epi_companies(id) ON DELETE CASCADE,
    company_name TEXT NOT NULL,  -- Denormalized

    -- Entry event
    event_type TEXT NOT NULL,  -- 'first_drug', 'acquisition', 'partnership', 'ipo', 'bankruptcy'
    event_description TEXT,

    -- Related entities
    drug_id UUID REFERENCES epi_drugs(id),
    drug_name TEXT,
    target_id UUID REFERENCES epi_targets(id),
    target_symbol TEXT,

    -- Source
    source TEXT,
    source_url TEXT,
    notes TEXT,

    -- Timestamps
    event_date DATE NOT NULL,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_company_entry_history_company ON epi_company_entry_history(company_id);
CREATE INDEX idx_company_entry_history_date ON epi_company_entry_history(event_date DESC);
CREATE INDEX idx_company_entry_history_type ON epi_company_entry_history(event_type);

-- ============================================
-- Target Activity History (when targets gained/lost drugs)
-- ============================================
CREATE TABLE IF NOT EXISTS epi_target_activity_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    target_id UUID NOT NULL REFERENCES epi_targets(id) ON DELETE CASCADE,
    target_symbol TEXT NOT NULL,  -- Denormalized

    -- Activity event
    event_type TEXT NOT NULL,  -- 'drug_added', 'drug_removed', 'approval', 'trial_started'

    -- Related drug
    drug_id UUID REFERENCES epi_drugs(id),
    drug_name TEXT,
    phase INTEGER,

    -- Source
    source TEXT,
    source_url TEXT,
    notes TEXT,

    -- Timestamps
    event_date DATE NOT NULL,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_target_activity_history_target ON epi_target_activity_history(target_id);
CREATE INDEX idx_target_activity_history_date ON epi_target_activity_history(event_date DESC);

-- ============================================
-- Snapshot of current state (for change detection)
-- ============================================
CREATE TABLE IF NOT EXISTS epi_state_snapshot (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
    entity_type TEXT NOT NULL,  -- 'drug', 'target', 'company'
    entity_id UUID NOT NULL,

    -- State data (JSON for flexibility)
    state_data JSONB NOT NULL,

    -- Hash for quick comparison
    state_hash TEXT NOT NULL,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(snapshot_date, entity_type, entity_id)
);

CREATE INDEX idx_state_snapshot_date ON epi_state_snapshot(snapshot_date DESC);
CREATE INDEX idx_state_snapshot_entity ON epi_state_snapshot(entity_type, entity_id);

-- ============================================
-- Enable RLS
-- ============================================
ALTER TABLE epi_drug_phase_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE epi_company_entry_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE epi_target_activity_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE epi_state_snapshot ENABLE ROW LEVEL SECURITY;

-- Public read access for all history tables
CREATE POLICY "Public read for drug phase history" ON epi_drug_phase_history
    FOR SELECT USING (true);

CREATE POLICY "Public read for company entry history" ON epi_company_entry_history
    FOR SELECT USING (true);

CREATE POLICY "Public read for target activity history" ON epi_target_activity_history
    FOR SELECT USING (true);

CREATE POLICY "Public read for state snapshot" ON epi_state_snapshot
    FOR SELECT USING (true);

-- Service role write access
CREATE POLICY "Service role write for drug phase history" ON epi_drug_phase_history
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role write for company entry history" ON epi_company_entry_history
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role write for target activity history" ON epi_target_activity_history
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role write for state snapshot" ON epi_state_snapshot
    FOR ALL USING (auth.role() = 'service_role');
