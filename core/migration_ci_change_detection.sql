-- CI Platform: Change Detection & Digest System
-- Week 2 Migration
-- Run this in Supabase Dashboard > SQL Editor

-- ============================================================
-- Table 1: ci_change_log
-- Tracks every change across all entities for audit + digest
-- ============================================================

CREATE TABLE IF NOT EXISTS ci_change_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What changed
    entity_type TEXT NOT NULL,  -- 'drug', 'trial', 'target', 'company', 'patent', 'news'
    entity_id TEXT,             -- UUID or string ID of the entity
    entity_name TEXT,           -- Human-readable name for display

    -- Change details
    change_type TEXT NOT NULL,  -- 'phase_change', 'status_change', 'new_entity', 'score_change', 'date_change', 'approval'
    field_changed TEXT,         -- Which field changed (e.g., 'max_phase', 'status', 'primary_completion_date')
    old_value TEXT,             -- Previous value (NULL for new entities)
    new_value TEXT,             -- New value
    change_summary TEXT,        -- Human-readable summary (e.g., "Phase 2 → Phase 3")

    -- Significance for alerting (determines who gets notified)
    significance TEXT NOT NULL DEFAULT 'low',  -- 'critical', 'high', 'medium', 'low'

    -- Source tracking
    source TEXT,                -- 'ctgov', 'fda', 'news', 'patent', 'etl', 'manual'
    source_url TEXT,            -- Link to source (NCT ID URL, FDA page, etc.)

    -- Related entities (for filtering)
    related_drug_id UUID,
    related_target_id UUID,
    related_company_id UUID,

    -- Timestamps
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Digest tracking
    digest_sent BOOLEAN DEFAULT FALSE,
    digest_sent_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT valid_significance CHECK (significance IN ('critical', 'high', 'medium', 'low')),
    CONSTRAINT valid_change_type CHECK (change_type IN (
        'phase_change', 'status_change', 'new_entity', 'score_change',
        'date_change', 'approval', 'termination', 'acquisition', 'patent_filed'
    ))
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_change_log_entity ON ci_change_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_change_log_significance ON ci_change_log(significance);
CREATE INDEX IF NOT EXISTS idx_change_log_detected ON ci_change_log(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_change_log_digest_pending ON ci_change_log(digest_sent, detected_at) WHERE digest_sent = FALSE;
CREATE INDEX IF NOT EXISTS idx_change_log_drug ON ci_change_log(related_drug_id) WHERE related_drug_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_change_log_target ON ci_change_log(related_target_id) WHERE related_target_id IS NOT NULL;

-- ============================================================
-- Table 2: ci_user_digest_prefs
-- User preferences for digest delivery
-- ============================================================

CREATE TABLE IF NOT EXISTS ci_user_digest_prefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User identification (can be email-based or Supabase Auth)
    user_id UUID,               -- Supabase Auth user ID (optional)
    email TEXT NOT NULL UNIQUE, -- Email for digest delivery
    name TEXT,                  -- Display name

    -- Digest frequency settings
    digest_frequency TEXT NOT NULL DEFAULT 'weekly',  -- 'daily', 'weekly', 'monthly', 'never'
    digest_day INTEGER DEFAULT 1,       -- For weekly: 0=Sunday, 1=Monday, ..., 6=Saturday
    digest_hour INTEGER DEFAULT 9,      -- Hour of day (0-23) in user's timezone
    digest_timezone TEXT DEFAULT 'America/New_York',

    -- Content filters
    min_significance TEXT DEFAULT 'low',  -- Only include changes >= this level
    entity_types TEXT[] DEFAULT ARRAY['drug', 'trial', 'target'],  -- Entity types to include

    -- Watchlist filter (if set, only changes to watched entities)
    watched_drug_ids UUID[],
    watched_target_ids UUID[],
    watched_company_ids UUID[],
    filter_to_watchlist BOOLEAN DEFAULT FALSE,  -- If true, only show watched entities

    -- Notification channels
    slack_webhook_url TEXT,     -- Optional Slack integration

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    verification_token TEXT,

    -- Tracking
    last_digest_sent TIMESTAMPTZ,
    total_digests_sent INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_frequency CHECK (digest_frequency IN ('daily', 'weekly', 'monthly', 'never')),
    CONSTRAINT valid_min_sig CHECK (min_significance IN ('critical', 'high', 'medium', 'low')),
    CONSTRAINT valid_day CHECK (digest_day >= 0 AND digest_day <= 6),
    CONSTRAINT valid_hour CHECK (digest_hour >= 0 AND digest_hour <= 23)
);

-- Index for finding users due for digest
CREATE INDEX IF NOT EXISTS idx_digest_prefs_active ON ci_user_digest_prefs(is_active, digest_frequency) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_digest_prefs_email ON ci_user_digest_prefs(email);

-- ============================================================
-- Table 3: ci_digest_history
-- Track sent digests for auditing and resend capability
-- ============================================================

CREATE TABLE IF NOT EXISTS ci_digest_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Recipient
    user_id UUID REFERENCES ci_user_digest_prefs(id),
    email TEXT NOT NULL,

    -- Content
    digest_type TEXT NOT NULL,  -- 'weekly', 'daily', 'monthly', 'alert'
    change_count INTEGER NOT NULL,
    change_ids UUID[],          -- References to ci_change_log entries included

    -- Delivery
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    delivery_status TEXT DEFAULT 'sent',  -- 'sent', 'delivered', 'bounced', 'failed'
    resend_message_id TEXT,     -- Resend API message ID for tracking

    -- Email content (for debugging/resend)
    subject TEXT,
    html_preview TEXT,          -- First 500 chars of HTML for preview

    -- Metrics
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,

    CONSTRAINT valid_delivery CHECK (delivery_status IN ('sent', 'delivered', 'bounced', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_digest_history_user ON ci_digest_history(user_id, sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_digest_history_email ON ci_digest_history(email, sent_at DESC);

-- ============================================================
-- Table 4: ci_entity_snapshots
-- Store daily snapshots for change detection comparison
-- ============================================================

CREATE TABLE IF NOT EXISTS ci_entity_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Entity identification
    entity_type TEXT NOT NULL,  -- 'drug', 'trial', 'target'
    entity_id TEXT NOT NULL,

    -- Snapshot data (JSON blob of key fields)
    snapshot_data JSONB NOT NULL,

    -- Timing
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint: one snapshot per entity per day
    UNIQUE(entity_type, entity_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_lookup ON ci_entity_snapshots(entity_type, entity_id, snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_snapshots_date ON ci_entity_snapshots(snapshot_date);

-- ============================================================
-- Helper function: Log a change with auto-generated summary
-- ============================================================

CREATE OR REPLACE FUNCTION log_entity_change(
    p_entity_type TEXT,
    p_entity_id TEXT,
    p_entity_name TEXT,
    p_change_type TEXT,
    p_field_changed TEXT,
    p_old_value TEXT,
    p_new_value TEXT,
    p_significance TEXT DEFAULT 'low',
    p_source TEXT DEFAULT 'etl',
    p_source_url TEXT DEFAULT NULL,
    p_related_drug_id UUID DEFAULT NULL,
    p_related_target_id UUID DEFAULT NULL,
    p_related_company_id UUID DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_change_id UUID;
    v_summary TEXT;
BEGIN
    -- Generate human-readable summary
    IF p_old_value IS NULL THEN
        v_summary := format('New %s: %s', p_entity_type, p_entity_name);
    ELSIF p_change_type = 'phase_change' THEN
        v_summary := format('%s: Phase %s → Phase %s', p_entity_name, p_old_value, p_new_value);
    ELSIF p_change_type = 'status_change' THEN
        v_summary := format('%s: %s → %s', p_entity_name, p_old_value, p_new_value);
    ELSIF p_change_type = 'date_change' THEN
        v_summary := format('%s: %s changed from %s to %s', p_entity_name, p_field_changed, p_old_value, p_new_value);
    ELSE
        v_summary := format('%s: %s changed', p_entity_name, p_field_changed);
    END IF;

    INSERT INTO ci_change_log (
        entity_type, entity_id, entity_name, change_type, field_changed,
        old_value, new_value, change_summary, significance, source, source_url,
        related_drug_id, related_target_id, related_company_id
    ) VALUES (
        p_entity_type, p_entity_id, p_entity_name, p_change_type, p_field_changed,
        p_old_value, p_new_value, v_summary, p_significance, p_source, p_source_url,
        p_related_drug_id, p_related_target_id, p_related_company_id
    ) RETURNING id INTO v_change_id;

    RETURN v_change_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- View: Pending digest changes (not yet sent)
-- ============================================================

CREATE OR REPLACE VIEW ci_pending_changes AS
SELECT
    cl.*,
    CASE
        WHEN cl.significance = 'critical' THEN 1
        WHEN cl.significance = 'high' THEN 2
        WHEN cl.significance = 'medium' THEN 3
        ELSE 4
    END as significance_order
FROM ci_change_log cl
WHERE cl.digest_sent = FALSE
ORDER BY significance_order, detected_at DESC;

-- ============================================================
-- Seed: Add a test user for digest (pilldreams admin)
-- ============================================================

INSERT INTO ci_user_digest_prefs (email, name, digest_frequency, min_significance, is_active, email_verified)
VALUES ('admin@pilldreams.io', 'Pilldreams Admin', 'weekly', 'medium', TRUE, TRUE)
ON CONFLICT (email) DO NOTHING;

-- ============================================================
-- Grant permissions (adjust as needed for your Supabase setup)
-- ============================================================

-- Enable RLS
ALTER TABLE ci_change_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE ci_user_digest_prefs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ci_digest_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE ci_entity_snapshots ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY "Service role has full access to change_log" ON ci_change_log
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to digest_prefs" ON ci_user_digest_prefs
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to digest_history" ON ci_digest_history
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to snapshots" ON ci_entity_snapshots
    FOR ALL USING (auth.role() = 'service_role');

-- Allow anon to read changes (for public dashboard)
CREATE POLICY "Anon can read changes" ON ci_change_log
    FOR SELECT USING (TRUE);

COMMENT ON TABLE ci_change_log IS 'Tracks all changes across entities for audit trail and digest generation';
COMMENT ON TABLE ci_user_digest_prefs IS 'User preferences for receiving change digest emails';
COMMENT ON TABLE ci_digest_history IS 'History of sent digests for tracking and resend capability';
COMMENT ON TABLE ci_entity_snapshots IS 'Daily snapshots of entity state for change detection';
