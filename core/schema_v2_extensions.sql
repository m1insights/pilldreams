-- ============================================================================
-- PILLDREAMS SCHEMA v2 EXTENSIONS
-- Backward-compatible additions for epigenetic editing, IO, resistance, patents
-- Run this AFTER the base schema is in place
-- ============================================================================

-- ============================================================================
-- 1. EXTEND EPI_DRUGS: add modality + flags
-- ============================================================================

-- Add modality column (small_molecule, epigenetic_editor, antibody)
ALTER TABLE epi_drugs
ADD COLUMN IF NOT EXISTS modality TEXT NOT NULL DEFAULT 'small_molecule';

-- Add epi-IO flag (immunomodulation relevance)
ALTER TABLE epi_drugs
ADD COLUMN IF NOT EXISTS is_epi_io BOOLEAN NOT NULL DEFAULT FALSE;

-- Add NSD2-targeted flag
ALTER TABLE epi_drugs
ADD COLUMN IF NOT EXISTS is_nsd2_targeted BOOLEAN NOT NULL DEFAULT FALSE;

-- ============================================================================
-- 2. EXTEND EPI_TARGETS: add new annotations
-- ============================================================================

-- IO exhaustion axis (T-cell exhaustion / immunomodulation)
ALTER TABLE epi_targets
ADD COLUMN IF NOT EXISTS io_exhaustion_axis BOOLEAN NOT NULL DEFAULT FALSE;

-- Epigenetic resistance role
ALTER TABLE epi_targets
ADD COLUMN IF NOT EXISTS epi_resistance_role TEXT NULL;

-- Aging clock relevance
ALTER TABLE epi_targets
ADD COLUMN IF NOT EXISTS aging_clock_relevance TEXT NULL;

-- ============================================================================
-- 3. NEW TABLE: EPI_EDITING_ASSETS (CRISPR/TALE epigenetic editors)
-- ============================================================================

CREATE TABLE IF NOT EXISTS epi_editing_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    sponsor TEXT,
    modality TEXT NOT NULL DEFAULT 'epigenetic_editor',
    delivery_type TEXT,                    -- 'LNP_mRNA', 'AAV', 'RNP'
    dbd_type TEXT,                         -- 'CRISPR_dCas9', 'TALE', 'ZF'
    effector_type TEXT,                    -- 'writer', 'eraser', 'indirect_repressor', 'combo'
    effector_domains JSONB,                -- ['DNMT3A','DNMT3L','KRAB']
    target_gene_symbol TEXT NOT NULL,
    target_id UUID REFERENCES epi_targets(id),
    primary_indication_id UUID REFERENCES epi_indications(id),
    phase INTEGER,                         -- 1,2,3,4 or NULL for preclinical
    status TEXT DEFAULT 'preclinical',     -- 'preclinical','clinical','approved','discontinued'
    description TEXT,
    source_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_editing_assets_target ON epi_editing_assets(target_id);
CREATE INDEX IF NOT EXISTS idx_editing_assets_indication ON epi_editing_assets(primary_indication_id);
CREATE INDEX IF NOT EXISTS idx_editing_assets_sponsor ON epi_editing_assets(sponsor);

-- ============================================================================
-- 4. NEW TABLE: EPI_EDITING_SCORES
-- ============================================================================

CREATE TABLE IF NOT EXISTS epi_editing_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    editing_asset_id UUID NOT NULL REFERENCES epi_editing_assets(id) ON DELETE CASCADE,
    indication_id UUID REFERENCES epi_indications(id),
    target_bio_score REAL,                 -- 0-100, from Open Targets
    editing_modality_score REAL,           -- 0-100, rule-based
    durability_score REAL,                 -- 0-100, from preclinical data
    total_editing_score REAL,              -- 0-100, weighted composite
    last_computed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(editing_asset_id, indication_id)
);

CREATE INDEX IF NOT EXISTS idx_editing_scores_asset ON epi_editing_scores(editing_asset_id);

-- ============================================================================
-- 5. NEW TABLE: EPI_PATENTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS epi_patents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patent_number TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    assignee TEXT,
    first_inventor TEXT,
    pub_date DATE,
    category TEXT,                         -- 'epi_editor','epi_therapy','epi_diagnostic','epi_io','epi_tool'
    abstract_snippet TEXT,
    related_target_symbols TEXT[],
    related_drug_ids UUID[],
    related_editing_asset_ids UUID[],
    source_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patents_category ON epi_patents(category);
CREATE INDEX IF NOT EXISTS idx_patents_assignee ON epi_patents(assignee);
CREATE INDEX IF NOT EXISTS idx_patents_pub_date ON epi_patents(pub_date DESC);

-- ============================================================================
-- 6. NEW TABLE: EPI_NEWS (AI-analyzed research feed)
-- ============================================================================

CREATE TABLE IF NOT EXISTS epi_news (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT,                           -- 'Nature','NRDD','BioSpace','PubMed'
    title TEXT NOT NULL,
    url TEXT,
    pub_date DATE,
    raw_text TEXT,
    category TEXT,                         -- 'epi_drug','epi_editing','epi_io','epi_resistance','epi_aging','other'
    related_drug_ids UUID[],
    related_target_ids UUID[],
    related_editing_asset_ids UUID[],
    related_company_ids UUID[],
    ai_summary TEXT,
    ai_impact_flag TEXT,                   -- 'confidence_up','confidence_down','no_change','unknown'
    ai_extracted_entities JSONB,           -- {drugs: [], targets: [], companies: []}
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_news_category ON epi_news(category);
CREATE INDEX IF NOT EXISTS idx_news_pub_date ON epi_news(pub_date DESC);
CREATE INDEX IF NOT EXISTS idx_news_source ON epi_news(source);

-- ============================================================================
-- 7. LINK TABLE: EPI_COMPANY_EDITING_ASSETS
-- ============================================================================

CREATE TABLE IF NOT EXISTS epi_company_editing_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES epi_companies(id) ON DELETE CASCADE,
    editing_asset_id UUID NOT NULL REFERENCES epi_editing_assets(id) ON DELETE CASCADE,
    relationship_type TEXT DEFAULT 'developer',  -- 'developer','licensor','partner'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(company_id, editing_asset_id)
);

-- ============================================================================
-- 8. VIEW: V_EDITING_ASSETS_FULL (for API responses)
-- ============================================================================

CREATE OR REPLACE VIEW v_editing_assets_full AS
SELECT
    ea.id,
    ea.name,
    ea.sponsor,
    ea.modality,
    ea.delivery_type,
    ea.dbd_type,
    ea.effector_type,
    ea.effector_domains,
    ea.target_gene_symbol,
    ea.phase,
    ea.status,
    ea.description,
    t.id AS target_id,
    t.symbol AS target_symbol,
    t.family AS target_family,
    t.class AS target_class,
    i.id AS indication_id,
    i.name AS indication_name,
    i.efo_id AS indication_efo_id,
    es.target_bio_score,
    es.editing_modality_score,
    es.durability_score,
    es.total_editing_score,
    ea.created_at,
    ea.updated_at
FROM epi_editing_assets ea
LEFT JOIN epi_targets t ON ea.target_id = t.id
LEFT JOIN epi_indications i ON ea.primary_indication_id = i.id
LEFT JOIN epi_editing_scores es ON es.editing_asset_id = ea.id AND es.indication_id = ea.primary_indication_id;

-- ============================================================================
-- 9. VIEW: V_TARGETS_ENRICHED (with new annotations)
-- ============================================================================

CREATE OR REPLACE VIEW v_targets_enriched AS
SELECT
    t.*,
    COUNT(DISTINCT dt.drug_id) AS drug_count,
    COUNT(DISTINCT ea.id) AS editing_asset_count,
    ARRAY_AGG(DISTINCT d.name) FILTER (WHERE d.name IS NOT NULL) AS drug_names
FROM epi_targets t
LEFT JOIN epi_drug_targets dt ON dt.target_id = t.id
LEFT JOIN epi_drugs d ON d.id = dt.drug_id
LEFT JOIN epi_editing_assets ea ON ea.target_id = t.id
GROUP BY t.id;

-- ============================================================================
-- 10. COMMENTS for documentation
-- ============================================================================

COMMENT ON TABLE epi_editing_assets IS 'Epigenetic editing programs (CRISPR/TALE/ZF-based)';
COMMENT ON COLUMN epi_editing_assets.dbd_type IS 'DNA-binding domain: CRISPR_dCas9, TALE, ZF';
COMMENT ON COLUMN epi_editing_assets.effector_domains IS 'JSON array of effector domains like DNMT3A, DNMT3L, KRAB';

COMMENT ON TABLE epi_patents IS 'Patent filings related to epigenetic drugs and editors';
COMMENT ON COLUMN epi_patents.category IS 'epi_editor, epi_therapy, epi_diagnostic, epi_io, epi_tool';

COMMENT ON TABLE epi_news IS 'AI-analyzed news and research articles';
COMMENT ON COLUMN epi_news.ai_impact_flag IS 'confidence_up, confidence_down, no_change, unknown';

COMMENT ON COLUMN epi_targets.io_exhaustion_axis IS 'TRUE if target involved in T-cell exhaustion/IO axis';
COMMENT ON COLUMN epi_targets.epi_resistance_role IS 'Role in epigenetic resistance (HCC_resistance, LUAD_TKI_resistance, etc.)';
COMMENT ON COLUMN epi_targets.aging_clock_relevance IS 'Relevance to epigenetic aging clocks';

COMMENT ON COLUMN epi_drugs.modality IS 'Drug modality: small_molecule, epigenetic_editor, antibody';
COMMENT ON COLUMN epi_drugs.is_epi_io IS 'TRUE if drug has epigenetic immunomodulation relevance';
COMMENT ON COLUMN epi_drugs.is_nsd2_targeted IS 'TRUE if primary target is NSD2';
