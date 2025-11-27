-- Add description to company table
ALTER TABLE company ADD COLUMN IF NOT EXISTS description TEXT;

-- Add source_url to company_drug table for AI verification
ALTER TABLE company_drug ADD COLUMN IF NOT EXISTS source_url TEXT;
ALTER TABLE company_drug ADD COLUMN IF NOT EXISTS confidence_score NUMERIC; -- 0.0 to 1.0
