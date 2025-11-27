-- Table to store Target-Disease associations from Open Targets
CREATE TABLE IF NOT EXISTS target_disease_association (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_id UUID REFERENCES target(id) ON DELETE CASCADE,
    disease_name TEXT NOT NULL,
    efo_id TEXT, -- Open Targets Disease ID
    association_score NUMERIC, -- 0.0 to 1.0
    evidence_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(target_id, disease_name)
);

CREATE INDEX IF NOT EXISTS idx_target_disease_score ON target_disease_association(association_score);
