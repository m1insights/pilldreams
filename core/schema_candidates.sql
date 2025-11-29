-- Drug Candidates Staging Table
-- Stores potential drug candidates from Open Targets for review before promotion to epi_drugs

DROP TABLE IF EXISTS epi_drug_candidates CASCADE;

CREATE TABLE epi_drug_candidates (
  id SERIAL PRIMARY KEY,

  -- Drug identifiers
  ot_drug_id TEXT NOT NULL,
  chembl_id TEXT,
  name TEXT NOT NULL,

  -- Drug properties
  drug_type TEXT,                    -- Small molecule, Antibody, etc.
  max_clinical_phase FLOAT,          -- 0-4 (4 = approved)

  -- Target link (which of our 67 targets led us here)
  source_target_id UUID REFERENCES epi_targets(id),
  source_target_symbol TEXT,
  ot_target_id TEXT,                 -- Open Targets target ID
  mechanism_of_action TEXT,

  -- Indication info (from OT)
  indication_efo_id TEXT,
  indication_name TEXT,
  indication_phase FLOAT,            -- Phase for this specific indication

  -- Status tracking
  status TEXT DEFAULT 'pending',     -- pending, approved, rejected, duplicate
  review_notes TEXT,

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  -- Unique constraint: one row per drug-target-indication combo
  UNIQUE(ot_drug_id, ot_target_id, indication_efo_id)
);

-- Indexes for filtering and deduplication
CREATE INDEX idx_candidates_drug ON epi_drug_candidates(ot_drug_id);
CREATE INDEX idx_candidates_target ON epi_drug_candidates(source_target_id);
CREATE INDEX idx_candidates_status ON epi_drug_candidates(status);
CREATE INDEX idx_candidates_phase ON epi_drug_candidates(max_clinical_phase);
CREATE INDEX idx_candidates_drug_type ON epi_drug_candidates(drug_type);

-- View for quick summary by drug (deduped)
CREATE OR REPLACE VIEW v_drug_candidates_summary AS
SELECT
  ot_drug_id,
  name,
  drug_type,
  max_clinical_phase,
  COUNT(DISTINCT source_target_symbol) as target_count,
  STRING_AGG(DISTINCT source_target_symbol, ', ' ORDER BY source_target_symbol) as targets,
  COUNT(DISTINCT indication_name) as indication_count,
  STRING_AGG(DISTINCT indication_name, ', ' ORDER BY indication_name) as indications,
  MAX(indication_phase) as best_phase,
  MIN(created_at) as first_seen
FROM epi_drug_candidates
WHERE status = 'pending'
GROUP BY ot_drug_id, name, drug_type, max_clinical_phase
ORDER BY max_clinical_phase DESC, target_count DESC;

COMMENT ON TABLE epi_drug_candidates IS 'Staging table for drug candidates from Open Targets. Review and promote to epi_drugs.';
