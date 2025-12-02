-- ============================================================================
-- NEWS STAGING TABLE
-- Articles fetched from RSS/APIs land here for admin review in Supabase
-- ============================================================================

-- Drop existing table if needed (careful in production!)
-- DROP TABLE IF EXISTS epi_news_staging;

CREATE TABLE IF NOT EXISTS epi_news_staging (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source metadata
    source TEXT NOT NULL,                    -- 'nature_drug_discovery', 'pubmed', 'biospace', 'company_pr'
    source_url TEXT NOT NULL,                -- Original article URL
    source_id TEXT,                          -- RSS GUID or PubMed ID for deduplication

    -- Article content (legally safe - titles and abstracts are public)
    title TEXT NOT NULL,
    abstract TEXT,                           -- Abstract/summary from RSS (not full article)
    pub_date DATE,
    authors TEXT[],

    -- AI-generated analysis (Gemini)
    ai_summary TEXT,                         -- 2-3 sentence summary
    ai_category TEXT,                        -- 'epi_drug', 'epi_editing', 'epi_io', 'clinical_trial', 'acquisition', 'other'
    ai_impact_flag TEXT,                     -- 'bullish', 'bearish', 'neutral', 'unknown'
    ai_extracted_entities JSONB,             -- {"drugs": ["tazemetostat"], "targets": ["EZH2"], "companies": ["Ipsen"]}
    ai_confidence REAL,                      -- 0-1 confidence in extraction

    -- Entity linking (after AI extraction, link to our DB)
    linked_drug_ids UUID[],
    linked_target_ids UUID[],
    linked_company_ids UUID[],

    -- Admin workflow (YOU edit these in Supabase Table Editor)
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'approved', 'rejected', 'actioned'
    admin_notes TEXT,                        -- Your notes/edits
    admin_action_taken TEXT,                 -- 'published', 'updated_drug_phase', 'added_indication', etc.
    reviewed_at TIMESTAMPTZ,
    reviewed_by TEXT,                        -- Your name/email

    -- Timestamps
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_news_staging_status ON epi_news_staging(status);
CREATE INDEX IF NOT EXISTS idx_news_staging_source ON epi_news_staging(source);
CREATE INDEX IF NOT EXISTS idx_news_staging_pub_date ON epi_news_staging(pub_date DESC);
CREATE INDEX IF NOT EXISTS idx_news_staging_category ON epi_news_staging(ai_category);

-- Unique constraint to prevent duplicate articles
CREATE UNIQUE INDEX IF NOT EXISTS idx_news_staging_source_id ON epi_news_staging(source, source_id) WHERE source_id IS NOT NULL;

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_news_staging_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_news_staging_updated ON epi_news_staging;
CREATE TRIGGER trigger_news_staging_updated
    BEFORE UPDATE ON epi_news_staging
    FOR EACH ROW
    EXECUTE FUNCTION update_news_staging_timestamp();

-- Comments for documentation
COMMENT ON TABLE epi_news_staging IS 'News articles awaiting admin review. Approve in Supabase Table Editor.';
COMMENT ON COLUMN epi_news_staging.status IS 'pending=needs review, approved=show to users, rejected=hide, actioned=triggered DB update';
COMMENT ON COLUMN epi_news_staging.ai_impact_flag IS 'bullish=positive for thesis, bearish=negative, neutral=informational';
COMMENT ON COLUMN epi_news_staging.admin_action_taken IS 'What you did: published, updated_drug_phase, added_indication, etc.';


-- ============================================================================
-- FACT CHECK LOG TABLE
-- Tracks Perplexity API verifications for audit trail
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_check_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What was checked
    entity_type TEXT NOT NULL,               -- 'drug', 'target', 'company'
    entity_id UUID NOT NULL,
    entity_name TEXT NOT NULL,

    -- What we claimed (our DB state at check time)
    our_data JSONB NOT NULL,                 -- Snapshot of our record

    -- What Perplexity returned
    perplexity_response JSONB,               -- Raw API response
    perplexity_summary TEXT,                 -- Parsed summary

    -- Diff analysis
    discrepancies JSONB,                     -- {"field": "phase", "ours": 3, "theirs": 4, "action_needed": true}
    has_discrepancies BOOLEAN DEFAULT FALSE,

    -- Resolution
    status TEXT DEFAULT 'pending',           -- 'pending', 'confirmed', 'updated', 'disputed'
    resolution_notes TEXT,
    resolved_at TIMESTAMPTZ,
    resolved_by TEXT,

    -- Timestamps
    checked_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fact_check_entity ON fact_check_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_fact_check_status ON fact_check_log(status);
CREATE INDEX IF NOT EXISTS idx_fact_check_discrepancies ON fact_check_log(has_discrepancies) WHERE has_discrepancies = TRUE;

COMMENT ON TABLE fact_check_log IS 'Audit trail of Perplexity fact-checks on drugs/targets/companies';
