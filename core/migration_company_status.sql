-- Migration: Add status column to epi_companies
-- Date: 2025-12-01
-- Purpose: Track acquired, delisted, and bankrupt companies

-- Add status column (active, acquired, delisted, bankrupt)
ALTER TABLE epi_companies
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';

-- Add acquirer column to track who acquired the company
ALTER TABLE epi_companies
ADD COLUMN IF NOT EXISTS acquirer TEXT;

-- Add acquisition_date column
ALTER TABLE epi_companies
ADD COLUMN IF NOT EXISTS acquisition_date DATE;

-- Add status_notes column for additional context
ALTER TABLE epi_companies
ADD COLUMN IF NOT EXISTS status_notes TEXT;

-- Create index on status for filtering
CREATE INDEX IF NOT EXISTS idx_epi_companies_status ON epi_companies(status);

-- Update existing companies to have 'active' status
UPDATE epi_companies SET status = 'active' WHERE status IS NULL;
