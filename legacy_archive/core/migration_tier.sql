-- Add tier column to drugs table
ALTER TABLE drugs ADD COLUMN IF NOT EXISTS tier VARCHAR(20) DEFAULT 'Bronze';
-- Update existing seed drugs to Gold (since we manually curated them)
-- Note: This is a simplification. Ideally we check approval status.
UPDATE drugs SET tier = 'Gold' WHERE tier IS NULL;
