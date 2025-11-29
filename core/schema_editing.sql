-- Epigenetic Editing Schema
-- Based on Nature Reviews Drug Discovery paper on Epigenetic Editing
-- Adds support for locus-targeted epigenetic editing therapies (CRISPR/ZF/TALE + effectors)

-- ============================================================
-- 1. Add modality to existing epi_drugs table (run as ALTER)
-- ============================================================
-- ALTER TABLE epi_drugs ADD COLUMN IF NOT EXISTS modality TEXT DEFAULT 'small_molecule';
-- UPDATE epi_drugs SET modality = 'small_molecule' WHERE modality IS NULL;

-- ============================================================
-- 2. Add editor-ready flags to epi_targets table (run as ALTER)
-- ============================================================
-- ALTER TABLE epi_targets ADD COLUMN IF NOT EXISTS editor_ready_status TEXT DEFAULT 'unknown';
-- ALTER TABLE epi_targets ADD COLUMN IF NOT EXISTS editor_notes TEXT;
-- COMMENT: editor_ready_status values: 'used_in_clinical_epiediting', 'strong_candidate', 'unknown'

-- ============================================================
-- 3. Epigenetic Editing Assets Table
-- ============================================================
CREATE TABLE IF NOT EXISTS epi_editing_assets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Basic Info
  name TEXT NOT NULL,                    -- Program name (e.g., OTX-2002, EvoETR-PCSK9)
  sponsor TEXT,                          -- Company (Omega Therapeutics, Tune, Epicrispr)
  modality TEXT DEFAULT 'epigenetic_editor',

  -- Delivery & Technology
  delivery_type TEXT,                    -- LNP_mRNA, AAV, other
  dbd_type TEXT,                         -- CRISPR_dCas9, CRISPR_dSaCas9, ZF, TALE, other
  effector_type TEXT,                    -- writer, eraser, indirect_repressor, indirect_activator, combo
  effector_domains JSONB,                -- ["KRAB","DNMT3A","DNMT3L"] or ["TET1"]

  -- Target Information
  target_gene_symbol TEXT,               -- MYC, PCSK9, HBV_genome, DMD, DUX4
  target_gene_id UUID REFERENCES epi_targets(id), -- Optional FK to targets table
  target_locus_description TEXT,         -- promoter, enhancer, allele-specific, viral cccDNA

  -- Clinical Info
  primary_indication TEXT,               -- Hepatocellular carcinoma, Hypercholesterolemia, etc.
  indication_id UUID REFERENCES epi_indications(id), -- Optional FK to indications
  phase INTEGER,                         -- 1, 2, 3, 4 (clinical phase)
  status TEXT DEFAULT 'unknown',         -- preclinical, clinical, completed, unknown

  -- Metadata
  description TEXT,
  mechanism_summary TEXT,                -- Brief mechanism description
  source_url TEXT,                       -- Link to company/trial info
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_epi_editing_assets_sponsor ON epi_editing_assets(sponsor);
CREATE INDEX IF NOT EXISTS idx_epi_editing_assets_target ON epi_editing_assets(target_gene_symbol);
CREATE INDEX IF NOT EXISTS idx_epi_editing_assets_status ON epi_editing_assets(status);
CREATE INDEX IF NOT EXISTS idx_epi_editing_assets_phase ON epi_editing_assets(phase);

-- ============================================================
-- 4. Epigenetic Editing Scores Table
-- ============================================================
-- Scoring framework for editing assets (different from ChemScore)
-- EditingScore = 0.5 * TargetBiologyScore + 0.3 * EditingModalityScore + 0.2 * DurabilityControlScore

CREATE TABLE IF NOT EXISTS epi_editing_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  editing_asset_id UUID NOT NULL REFERENCES epi_editing_assets(id) ON DELETE CASCADE,
  indication_id UUID REFERENCES epi_indications(id),

  -- Component Scores (0-100)
  target_bio_score FLOAT,                -- Target-disease biology score (from Open Targets)
  editing_modality_score FLOAT,          -- Based on delivery type, effector domains, maturity
  durability_score FLOAT,                -- Stability vs reversibility assessment

  -- Total Score
  total_editing_score FLOAT,             -- Weighted combination

  -- Score Metadata
  score_rationale TEXT,                  -- Brief explanation of scoring
  computed_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(editing_asset_id, indication_id)
);

CREATE INDEX IF NOT EXISTS idx_epi_editing_scores_asset ON epi_editing_scores(editing_asset_id);
CREATE INDEX IF NOT EXISTS idx_epi_editing_scores_indication ON epi_editing_scores(indication_id);
CREATE INDEX IF NOT EXISTS idx_epi_editing_scores_total ON epi_editing_scores(total_editing_score DESC);

-- ============================================================
-- 5. Editing Target Genes Table (for non-epi targets like PCSK9)
-- ============================================================
-- Some editing targets are not classic epigenetic enzymes (PCSK9, MYC, DUX4)
-- This table extends the target concept for editing-relevant genes

CREATE TABLE IF NOT EXISTS epi_editing_target_genes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Gene Info
  symbol TEXT NOT NULL UNIQUE,           -- PCSK9, MYC, HBV, DUX4, etc.
  full_name TEXT,
  ensembl_id TEXT,
  uniprot_id TEXT,

  -- Classification
  gene_category TEXT,                    -- oncogene, disease_gene, viral_target, other
  is_classic_epi_target BOOLEAN DEFAULT FALSE, -- Links to epi_targets if true
  epi_target_id UUID REFERENCES epi_targets(id), -- FK if it's also an epi target

  -- Editor Readiness
  editor_ready_status TEXT DEFAULT 'unknown', -- used_in_clinical_epiediting, strong_candidate, unknown
  editor_notes TEXT,                     -- Why this is a good/bad editing target
  lof_tolerance TEXT,                    -- tolerated, partial, not_tolerated, unknown

  -- Disease Relevance
  primary_disease_areas TEXT[],          -- Array of disease areas
  open_targets_score FLOAT,              -- Max association score from Open Targets

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_editing_target_genes_symbol ON epi_editing_target_genes(symbol);
CREATE INDEX IF NOT EXISTS idx_editing_target_genes_category ON epi_editing_target_genes(gene_category);

-- ============================================================
-- 6. Link table: Editing Assets to Target Genes (many-to-many)
-- ============================================================
CREATE TABLE IF NOT EXISTS epi_editing_asset_targets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  editing_asset_id UUID NOT NULL REFERENCES epi_editing_assets(id) ON DELETE CASCADE,
  target_gene_id UUID NOT NULL REFERENCES epi_editing_target_genes(id) ON DELETE CASCADE,
  is_primary_target BOOLEAN DEFAULT TRUE,
  mechanism_at_target TEXT,              -- What the editor does at this target
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(editing_asset_id, target_gene_id)
);

CREATE INDEX IF NOT EXISTS idx_editing_asset_targets_asset ON epi_editing_asset_targets(editing_asset_id);
CREATE INDEX IF NOT EXISTS idx_editing_asset_targets_gene ON epi_editing_asset_targets(target_gene_id);

-- ============================================================
-- 7. Views for easy querying
-- ============================================================

-- View: Editing assets with scores
CREATE OR REPLACE VIEW v_epi_editing_assets_scored AS
SELECT
  ea.*,
  es.target_bio_score,
  es.editing_modality_score,
  es.durability_score,
  es.total_editing_score,
  es.score_rationale
FROM epi_editing_assets ea
LEFT JOIN epi_editing_scores es ON ea.id = es.editing_asset_id;

-- View: Target genes with editing programs count
CREATE OR REPLACE VIEW v_epi_editing_target_genes_summary AS
SELECT
  tg.*,
  COUNT(DISTINCT eat.editing_asset_id) as editing_program_count
FROM epi_editing_target_genes tg
LEFT JOIN epi_editing_asset_targets eat ON tg.id = eat.target_gene_id
GROUP BY tg.id;
