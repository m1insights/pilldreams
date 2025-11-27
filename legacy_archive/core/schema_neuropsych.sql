-- ===============================================
-- Neuropsych Intelligence Platform Schema
-- ===============================================

-- 1. Drugs (Core Registry)
-- Stores the main drug entities with their high-level metadata
CREATE TABLE IF NOT EXISTS drugs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    chembl_id VARCHAR(50),
    synonyms TEXT[],
    drug_class VARCHAR(255),
    mechanism_summary TEXT,
    molecule_type VARCHAR(100),
    status VARCHAR(50), -- approved, phase1, phase2, phase3, discontinued
    indications_list TEXT[],
    innovation_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_drugs_name ON drugs(name);
CREATE INDEX IF NOT EXISTS idx_drugs_chembl_id ON drugs(chembl_id);

-- 2. Targets (Biological Targets)
-- Stores biological targets (proteins, receptors)
CREATE TABLE IF NOT EXISTS targets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(50) NOT NULL,
    uniprot_id VARCHAR(50),
    chembl_id VARCHAR(50),
    description TEXT,
    pathway VARCHAR(255),
    has_3d_structure BOOLEAN DEFAULT FALSE,
    evidence_score FLOAT, -- From OpenTargets
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_targets_symbol ON targets(symbol);
CREATE INDEX IF NOT EXISTS idx_targets_uniprot ON targets(uniprot_id);

-- 3. Drug-Targets (Junction)
-- Links drugs to targets with quantitative binding data
CREATE TABLE IF NOT EXISTS drug_targets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drug_id UUID REFERENCES drugs(id) ON DELETE CASCADE,
    target_id UUID REFERENCES targets(id) ON DELETE CASCADE,
    affinity_value FLOAT, -- Ki, IC50, Kd value
    affinity_unit VARCHAR(20), -- nM, uM
    affinity_type VARCHAR(20), -- Ki, IC50, Kd
    confidence_score FLOAT,
    role_on_target VARCHAR(100), -- agonist, antagonist, inhibitor, modulator
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_drug_targets_drug ON drug_targets(drug_id);
CREATE INDEX IF NOT EXISTS idx_drug_targets_target ON drug_targets(target_id);

-- 4. Clinical Trials (Pipeline)
-- Stores specific trial data for the drugs
CREATE TABLE IF NOT EXISTS clinical_trials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drug_id UUID REFERENCES drugs(id) ON DELETE CASCADE,
    nct_id VARCHAR(20) UNIQUE,
    phase VARCHAR(50),
    condition VARCHAR(255),
    status VARCHAR(50),
    start_date DATE,
    completion_date DATE,
    sponsor VARCHAR(255),
    source VARCHAR(50) DEFAULT 'clinicaltrials.gov',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_clinical_trials_drug ON clinical_trials(drug_id);
CREATE INDEX IF NOT EXISTS idx_clinical_trials_nct ON clinical_trials(nct_id);

-- 5. Adverse Events (Safety)
-- Stores safety signals and adverse event data
CREATE TABLE IF NOT EXISTS adverse_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drug_id UUID REFERENCES drugs(id) ON DELETE CASCADE,
    event_name VARCHAR(255),
    frequency FLOAT,
    seriousness_score FLOAT,
    source VARCHAR(50) DEFAULT 'openfda',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_adverse_events_drug ON adverse_events(drug_id);

-- 6. Publications (Evidence)
-- Stores publication counts and evidence maturity metrics
CREATE TABLE IF NOT EXISTS publications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drug_id UUID REFERENCES drugs(id) ON DELETE CASCADE,
    pubmed_count INT DEFAULT 0,
    rct_count INT DEFAULT 0,
    meta_analysis_count INT DEFAULT 0,
    latest_publication_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_publications_drug ON publications(drug_id);
