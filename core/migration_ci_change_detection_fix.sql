-- CI Platform: Change Detection - FIX MIGRATION
-- Run this if the main migration failed due to missing columns
-- This will add any missing columns to existing tables

-- ============================================================
-- Option 1: DROP AND RECREATE (cleanest - use if no data to preserve)
-- ============================================================

-- Uncomment these lines to drop and start fresh:
-- DROP TABLE IF EXISTS ci_digest_history CASCADE;
-- DROP TABLE IF EXISTS ci_user_digest_prefs CASCADE;
-- DROP TABLE IF EXISTS ci_entity_snapshots CASCADE;
-- DROP TABLE IF EXISTS ci_change_log CASCADE;
-- DROP VIEW IF EXISTS ci_pending_changes CASCADE;
-- DROP FUNCTION IF EXISTS log_entity_change CASCADE;

-- Then re-run the main migration: core/migration_ci_change_detection.sql

-- ============================================================
-- Option 2: ADD MISSING COLUMNS (use if you have data to preserve)
-- ============================================================

-- Add missing columns to ci_change_log if they don't exist
DO $$
BEGIN
    -- Add related_drug_id if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ci_change_log' AND column_name = 'related_drug_id'
    ) THEN
        ALTER TABLE ci_change_log ADD COLUMN related_drug_id UUID;
    END IF;

    -- Add related_target_id if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ci_change_log' AND column_name = 'related_target_id'
    ) THEN
        ALTER TABLE ci_change_log ADD COLUMN related_target_id UUID;
    END IF;

    -- Add related_company_id if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ci_change_log' AND column_name = 'related_company_id'
    ) THEN
        ALTER TABLE ci_change_log ADD COLUMN related_company_id UUID;
    END IF;

    -- Add change_summary if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ci_change_log' AND column_name = 'change_summary'
    ) THEN
        ALTER TABLE ci_change_log ADD COLUMN change_summary TEXT;
    END IF;
END $$;

-- Now create indexes (they'll succeed with columns present)
CREATE INDEX IF NOT EXISTS idx_change_log_entity ON ci_change_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_change_log_significance ON ci_change_log(significance);
CREATE INDEX IF NOT EXISTS idx_change_log_detected ON ci_change_log(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_change_log_digest_pending ON ci_change_log(digest_sent, detected_at) WHERE digest_sent = FALSE;
CREATE INDEX IF NOT EXISTS idx_change_log_drug ON ci_change_log(related_drug_id) WHERE related_drug_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_change_log_target ON ci_change_log(related_target_id) WHERE related_target_id IS NOT NULL;

-- ============================================================
-- Verify the fix
-- ============================================================
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'ci_change_log'
ORDER BY ordinal_position;
