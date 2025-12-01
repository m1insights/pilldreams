-- Migration: Add max_phase column to epi_drugs
-- This stores the maximum clinical trial phase from ChEMBL

ALTER TABLE epi_drugs
ADD COLUMN IF NOT EXISTS max_phase INTEGER;

-- Phase values:
-- 0 = Preclinical
-- 1 = Phase 1
-- 2 = Phase 2
-- 3 = Phase 3
-- 4 = Approved (FDA)

COMMENT ON COLUMN epi_drugs.max_phase IS 'Maximum clinical trial phase (0-4) from ChEMBL';
