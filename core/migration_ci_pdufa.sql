-- PDUFA Date Tracker Schema
-- Tracks FDA action dates for epigenetic oncology drug approvals
-- Created: 2025-12-02

-- ============================================
-- Table: ci_pdufa_dates
-- ============================================
-- Stores PDUFA dates for NDAs/BLAs under FDA review
-- Sources: FDA RSS feeds, press releases, SEC filings

CREATE TABLE IF NOT EXISTS ci_pdufa_dates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Drug identification
    drug_name TEXT NOT NULL,
    drug_id UUID REFERENCES epi_drugs(id),  -- Link to our drug table if exists
    chembl_id TEXT,

    -- Company information
    company_name TEXT NOT NULL,
    company_ticker TEXT,  -- For stock catalyst tracking

    -- FDA submission details
    application_type TEXT NOT NULL CHECK (application_type IN ('NDA', 'BLA', 'sNDA', 'sBLA')),
    application_number TEXT,  -- e.g., "NDA 216456"

    -- Target indication
    indication TEXT NOT NULL,
    indication_efo_id TEXT,  -- Link to EFO ontology

    -- PDUFA date tracking
    pdufa_date DATE NOT NULL,
    pdufa_date_type TEXT DEFAULT 'standard' CHECK (pdufa_date_type IN ('standard', 'priority', 'accelerated', 'breakthrough')),

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending',           -- Awaiting FDA decision
        'approved',          -- FDA approved
        'crl',               -- Complete Response Letter (rejection)
        'withdrawn',         -- Company withdrew application
        'extended',          -- FDA extended review
        'delayed'            -- Sponsor-requested delay
    )),

    -- Outcome details (filled after PDUFA date)
    outcome_date DATE,
    outcome_notes TEXT,

    -- Source tracking
    source TEXT NOT NULL CHECK (source IN ('fda_rss', 'press_release', 'sec_filing', 'ctgov', 'manual')),
    source_url TEXT,
    source_date TIMESTAMPTZ,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Prevent duplicates
    UNIQUE(drug_name, indication, pdufa_date)
);

-- ============================================
-- Table: ci_pdufa_history
-- ============================================
-- Tracks changes to PDUFA dates (extensions, delays, etc.)

CREATE TABLE IF NOT EXISTS ci_pdufa_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pdufa_id UUID NOT NULL REFERENCES ci_pdufa_dates(id) ON DELETE CASCADE,

    -- What changed
    change_type TEXT NOT NULL CHECK (change_type IN (
        'date_extended',     -- FDA extended review
        'date_delayed',      -- Sponsor requested delay
        'status_updated',    -- Status changed (approved, CRL, etc.)
        'info_updated'       -- Other info updated
    )),

    -- Old and new values
    old_value TEXT,
    new_value TEXT,

    -- Change source
    source TEXT,
    source_url TEXT,
    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- Indexes for performance
-- ============================================

CREATE INDEX IF NOT EXISTS idx_pdufa_date ON ci_pdufa_dates(pdufa_date);
CREATE INDEX IF NOT EXISTS idx_pdufa_status ON ci_pdufa_dates(status);
CREATE INDEX IF NOT EXISTS idx_pdufa_drug_id ON ci_pdufa_dates(drug_id);
CREATE INDEX IF NOT EXISTS idx_pdufa_company ON ci_pdufa_dates(company_ticker);
CREATE INDEX IF NOT EXISTS idx_pdufa_history_pdufa_id ON ci_pdufa_history(pdufa_id);

-- ============================================
-- Update trigger for updated_at
-- ============================================

CREATE OR REPLACE FUNCTION update_pdufa_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_pdufa_updated_at ON ci_pdufa_dates;
CREATE TRIGGER trigger_pdufa_updated_at
    BEFORE UPDATE ON ci_pdufa_dates
    FOR EACH ROW
    EXECUTE FUNCTION update_pdufa_updated_at();

-- ============================================
-- Comments
-- ============================================

COMMENT ON TABLE ci_pdufa_dates IS 'PDUFA dates for epigenetic oncology drug approvals';
COMMENT ON COLUMN ci_pdufa_dates.pdufa_date_type IS 'FDA review track: standard (10mo), priority (6mo), accelerated, breakthrough';
COMMENT ON COLUMN ci_pdufa_dates.status IS 'Current status: pending, approved, crl (rejection), withdrawn, extended, delayed';
COMMENT ON COLUMN ci_pdufa_dates.application_type IS 'NDA=small molecule, BLA=biologic, sNDA/sBLA=supplemental';
