-- ETL Refresh Log Table Enhancement
-- Makes entity_id optional and adds columns for pipeline-level logging
-- (news, patents, etc. don't have a specific entity_id)

-- Make entity_id nullable for pipeline-level runs
ALTER TABLE etl_refresh_log
ALTER COLUMN entity_id DROP NOT NULL;

-- Add new columns for richer tracking
ALTER TABLE etl_refresh_log
ADD COLUMN IF NOT EXISTS records_inserted INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS records_skipped INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS details JSONB;

-- Add index for querying by entity_type (pipeline-level queries)
CREATE INDEX IF NOT EXISTS idx_etl_log_entity_type ON etl_refresh_log(entity_type);
CREATE INDEX IF NOT EXISTS idx_etl_log_created_at ON etl_refresh_log(created_at DESC);

-- Comments
COMMENT ON COLUMN etl_refresh_log.entity_id IS 'UUID of specific entity (NULL for pipeline-level runs like news/patents)';
COMMENT ON COLUMN etl_refresh_log.records_inserted IS 'Number of new records inserted';
COMMENT ON COLUMN etl_refresh_log.records_skipped IS 'Number of records skipped (duplicates, filtered)';
COMMENT ON COLUMN etl_refresh_log.details IS 'Full stats JSON for debugging';

-- Example queries:
-- Pipeline-level: SELECT * FROM etl_refresh_log WHERE entity_type = 'news' ORDER BY created_at DESC LIMIT 10;
-- Entity-level: SELECT * FROM etl_refresh_log WHERE entity_type = 'target' AND entity_id = 'xxx';
-- Summary: SELECT entity_type, COUNT(*), SUM(records_inserted) FROM etl_refresh_log GROUP BY entity_type;
