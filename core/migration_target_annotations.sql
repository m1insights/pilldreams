-- ============================================================================
-- MIGRATION: Add Target-Level Annotations to epi_targets
-- ============================================================================
-- Run this in Supabase Dashboard > SQL Editor > New Query > Run
-- ============================================================================

-- Add IO exhaustion axis annotation
-- Targets that are relevant to T-cell exhaustion / IO resistance mechanisms
ALTER TABLE epi_targets ADD COLUMN IF NOT EXISTS io_exhaustion_axis BOOLEAN DEFAULT FALSE;

-- Add epigenetic resistance role annotation
-- Role in resistance mechanisms: 'primary_driver', 'secondary', 'modulator', NULL
ALTER TABLE epi_targets ADD COLUMN IF NOT EXISTS epi_resistance_role TEXT;

-- Add aging clock relevance annotation
-- Relevance to epigenetic aging clocks / longevity research
ALTER TABLE epi_targets ADD COLUMN IF NOT EXISTS aging_clock_relevance TEXT;

-- Add IO combination priority score
-- 0-100 score indicating priority for IO combination studies
ALTER TABLE epi_targets ADD COLUMN IF NOT EXISTS io_combo_priority INTEGER CHECK (io_combo_priority >= 0 AND io_combo_priority <= 100);

-- Add target annotation notes
ALTER TABLE epi_targets ADD COLUMN IF NOT EXISTS annotation_notes TEXT;

-- Create index for IO exhaustion queries
CREATE INDEX IF NOT EXISTS idx_targets_io_exhaustion ON epi_targets(io_exhaustion_axis) WHERE io_exhaustion_axis = TRUE;

-- Create index for resistance role queries
CREATE INDEX IF NOT EXISTS idx_targets_resistance_role ON epi_targets(epi_resistance_role) WHERE epi_resistance_role IS NOT NULL;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON COLUMN epi_targets.io_exhaustion_axis IS 'Target is relevant to T-cell exhaustion / IO resistance mechanisms';
COMMENT ON COLUMN epi_targets.epi_resistance_role IS 'Role in resistance: primary_driver, secondary, modulator';
COMMENT ON COLUMN epi_targets.aging_clock_relevance IS 'Relevance to epigenetic aging clocks';
COMMENT ON COLUMN epi_targets.io_combo_priority IS '0-100 priority score for IO combination studies';
COMMENT ON COLUMN epi_targets.annotation_notes IS 'Free text notes about target annotations';
