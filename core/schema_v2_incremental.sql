-- ============================================================================
-- PILLDREAMS SCHEMA v2 INCREMENTAL MIGRATION
-- Only adds missing columns/tables (backward-compatible)
-- ============================================================================

-- ============================================================================
-- 1. EXTEND EPI_DRUGS: add modality + flags
-- ============================================================================

ALTER TABLE epi_drugs
ADD COLUMN IF NOT EXISTS modality TEXT NOT NULL DEFAULT 'small_molecule';

ALTER TABLE epi_drugs
ADD COLUMN IF NOT EXISTS is_epi_io BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE epi_drugs
ADD COLUMN IF NOT EXISTS is_nsd2_targeted BOOLEAN NOT NULL DEFAULT FALSE;

-- ============================================================================
-- 2. EXTEND EPI_TARGETS: add new annotations
-- ============================================================================

ALTER TABLE epi_targets
ADD COLUMN IF NOT EXISTS io_exhaustion_axis BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE epi_targets
ADD COLUMN IF NOT EXISTS epi_resistance_role TEXT NULL;

ALTER TABLE epi_targets
ADD COLUMN IF NOT EXISTS aging_clock_relevance TEXT NULL;

-- ============================================================================
-- 3. NEW TABLE: EPI_PATENTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS epi_patents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patent_number TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    assignee TEXT,
    first_inventor TEXT,
    pub_date DATE,
    category TEXT,
    abstract_snippet TEXT,
    related_target_symbols TEXT[],
    related_drug_ids UUID[],
    related_editing_asset_ids UUID[],
    source_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patents_category ON epi_patents(category);
CREATE INDEX IF NOT EXISTS idx_patents_assignee ON epi_patents(assignee);

-- ============================================================================
-- 4. NEW TABLE: EPI_NEWS
-- ============================================================================

CREATE TABLE IF NOT EXISTS epi_news (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT,
    title TEXT NOT NULL,
    url TEXT,
    pub_date DATE,
    raw_text TEXT,
    category TEXT,
    related_drug_ids UUID[],
    related_target_ids UUID[],
    related_editing_asset_ids UUID[],
    related_company_ids UUID[],
    ai_summary TEXT,
    ai_impact_flag TEXT,
    ai_extracted_entities JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_news_category ON epi_news(category);
CREATE INDEX IF NOT EXISTS idx_news_pub_date ON epi_news(pub_date DESC);

-- ============================================================================
-- 5. NEW TABLE: EPI_EDITING_SCORES (if not exists)
-- ============================================================================

CREATE TABLE IF NOT EXISTS epi_editing_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    editing_asset_id UUID NOT NULL REFERENCES epi_editing_assets(id) ON DELETE CASCADE,
    indication_id UUID REFERENCES epi_indications(id),
    target_bio_score REAL,
    editing_modality_score REAL,
    durability_score REAL,
    total_editing_score REAL,
    last_computed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(editing_asset_id, indication_id)
);

CREATE INDEX IF NOT EXISTS idx_editing_scores_asset ON epi_editing_scores(editing_asset_id);
