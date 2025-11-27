-- Migration to add ChEMBL-specific columns to Target and DrugTarget tables

-- Add columns to Target table for ChEMBL data
ALTER TABLE target
ADD COLUMN IF NOT EXISTS target_chembl_id VARCHAR(50),
ADD COLUMN IF NOT EXISTS name VARCHAR(255),
ADD COLUMN IF NOT EXISTS target_type VARCHAR(100);

-- Create index on ChEMBL ID for faster lookups
CREATE INDEX IF NOT EXISTS idx_target_chembl ON target(target_chembl_id);

-- Add columns to DrugTarget table for binding affinity details
ALTER TABLE drugtarget
ADD COLUMN IF NOT EXISTS affinity_type VARCHAR(20),
ADD COLUMN IF NOT EXISTS measurement_count INTEGER;

-- Note:
-- - symbol and description columns remain for DrugBank/UniProt data
-- - name will be used for ChEMBL target preferred name
-- - target_type will store ChEMBL target classification (e.g., "SINGLE PROTEIN", "PROTEIN COMPLEX")
-- - affinity_type stores the measurement type (Ki, IC50, Kd, EC50)
-- - measurement_count tracks how many binding assays were aggregated
