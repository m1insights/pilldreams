-- ============================================================================
-- PILLDREAMS SCHEMA: EPI_COMBOS
-- Combination therapy tracking for epi+IO, epi+KRAS, epi+radiation strategies
-- ============================================================================
-- Run this in Supabase Dashboard > SQL Editor > New Query > Run
-- ============================================================================

-- Drop existing if needed for clean recreation
DROP TABLE IF EXISTS epi_combos CASCADE;

-- ============================================================================
-- EPI_COMBOS: Combination therapy strategies
-- ============================================================================

CREATE TABLE epi_combos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Combination label/category
    combo_label TEXT NOT NULL,              -- 'epi+IO', 'epi+KRAS', 'epi+radiation', etc.

    -- Epigenetic drug (required)
    epi_drug_id UUID NOT NULL REFERENCES epi_drugs(id) ON DELETE CASCADE,

    -- Partner drug (optional - if partner is also in our database)
    partner_drug_id UUID REFERENCES epi_drugs(id) ON DELETE SET NULL,

    -- Partner class (for external drugs or modalities not in our DB)
    partner_class TEXT,                     -- 'PD-1_inhibitor', 'KRAS_G12C_inhibitor', 'radiation', etc.
    partner_drug_name TEXT,                 -- e.g., 'PEMBROLIZUMAB', 'SOTORASIB'

    -- Indication context
    indication_id UUID NOT NULL REFERENCES epi_indications(id) ON DELETE CASCADE,

    -- Clinical development
    max_phase INTEGER CHECK (max_phase >= 0 AND max_phase <= 4),  -- 0=preclinical, 1-4=clinical phases
    nct_id TEXT,                            -- ClinicalTrials.gov identifier if applicable

    -- Provenance
    source TEXT,                            -- 'OpenTargets', 'PubMed', 'Review', 'CompanyPR', 'ClinicalTrials'
    source_url TEXT,
    notes TEXT,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT combo_has_partner CHECK (
        partner_drug_id IS NOT NULL OR partner_class IS NOT NULL
    )
);

-- Indexes for common queries
CREATE INDEX idx_combos_label ON epi_combos(combo_label);
CREATE INDEX idx_combos_epi_drug ON epi_combos(epi_drug_id);
CREATE INDEX idx_combos_partner_drug ON epi_combos(partner_drug_id) WHERE partner_drug_id IS NOT NULL;
CREATE INDEX idx_combos_partner_class ON epi_combos(partner_class) WHERE partner_class IS NOT NULL;
CREATE INDEX idx_combos_indication ON epi_combos(indication_id);
CREATE INDEX idx_combos_phase ON epi_combos(max_phase);

-- ============================================================================
-- VIEW: V_EPI_COMBOS_FULL (for API responses)
-- ============================================================================

CREATE OR REPLACE VIEW v_epi_combos_full AS
SELECT
    c.id,
    c.combo_label,
    c.epi_drug_id,
    ed.name AS epi_drug_name,
    ed.chembl_id AS epi_drug_chembl_id,
    c.partner_drug_id,
    pd.name AS partner_drug_name_db,
    COALESCE(pd.name, c.partner_drug_name) AS partner_drug_name,
    c.partner_class,
    c.indication_id,
    i.name AS indication_name,
    i.efo_id AS indication_efo_id,
    c.max_phase,
    c.nct_id,
    c.source,
    c.source_url,
    c.notes,
    c.created_at,
    c.updated_at
FROM epi_combos c
JOIN epi_drugs ed ON ed.id = c.epi_drug_id
LEFT JOIN epi_drugs pd ON pd.id = c.partner_drug_id
JOIN epi_indications i ON i.id = c.indication_id;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE epi_combos IS 'Combination therapy strategies involving epigenetic drugs';
COMMENT ON COLUMN epi_combos.combo_label IS 'Category: epi+IO, epi+KRAS, epi+radiation, etc.';
COMMENT ON COLUMN epi_combos.epi_drug_id IS 'The epigenetic drug in the combination (required)';
COMMENT ON COLUMN epi_combos.partner_drug_id IS 'Partner drug if it exists in epi_drugs table';
COMMENT ON COLUMN epi_combos.partner_class IS 'Partner class for external drugs (e.g., PD-1_inhibitor)';
COMMENT ON COLUMN epi_combos.max_phase IS 'Clinical phase: 0=preclinical, 1-4=clinical phases';
