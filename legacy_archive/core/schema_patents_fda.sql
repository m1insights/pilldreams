-- ===============================================
-- Patent Data & FDA Precedent Analysis Schema
-- ===============================================

-- Patent data from FDA Orange Book
CREATE TABLE IF NOT EXISTS patent (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drug_id UUID REFERENCES drug(id) ON DELETE CASCADE,
    patent_number VARCHAR(50) NOT NULL,
    patent_expire_date DATE,
    drug_substance_flag BOOLEAN DEFAULT FALSE,  -- Covers the drug molecule itself
    drug_product_flag BOOLEAN DEFAULT FALSE,     -- Covers the formulation
    use_code VARCHAR(10),                        -- Use patent code
    use_description TEXT,                        -- What the patent covers
    delist_requested BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patent_drug ON patent(drug_id);
CREATE INDEX IF NOT EXISTS idx_patent_expiry ON patent(patent_expire_date);

-- Exclusivity periods (regulatory moat beyond patents)
CREATE TABLE IF NOT EXISTS exclusivity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drug_id UUID REFERENCES drug(id) ON DELETE CASCADE,
    exclusivity_code VARCHAR(10),                -- e.g., NCE, ODE, PED
    exclusivity_date DATE,                       -- Expiration date
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_exclusivity_drug ON exclusivity(drug_id);

-- FDA approval precedent data (historical success rates)
CREATE TABLE IF NOT EXISTS fda_precedent (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    indication VARCHAR(255) NOT NULL,            -- Disease/condition
    phase_1_to_2_success_rate FLOAT,            -- Historical Phase I→II success rate
    phase_2_to_3_success_rate FLOAT,            -- Historical Phase II→III success rate
    phase_3_to_approval_success_rate FLOAT,     -- Historical Phase III→Approval success rate
    median_approval_time_months INT,             -- Median time from IND to approval
    n_drugs_analyzed INT,                        -- Sample size
    last_updated TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_precedent_indication ON fda_precedent(indication);

-- Drug approval probability (calculated per drug)
CREATE TABLE IF NOT EXISTS approval_probability (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drug_id UUID REFERENCES drug(id) ON DELETE CASCADE UNIQUE,
    current_phase VARCHAR(10),
    base_success_rate FLOAT,                     -- Historical rate for this phase + indication
    trial_quality_adjustment FLOAT,              -- Bonus/penalty based on trial design scores
    competitive_adjustment FLOAT,                -- Bonus/penalty based on competitive landscape
    final_probability FLOAT,                     -- Final calculated approval probability (0-1)
    confidence_level VARCHAR(20),                -- High, Medium, Low
    calculated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_approval_prob_drug ON approval_probability(drug_id);

-- Patent aggregate (summary per drug)
CREATE TABLE IF NOT EXISTS patentaggregate (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drug_id UUID REFERENCES drug(id) ON DELETE CASCADE UNIQUE,
    total_patents INT DEFAULT 0,
    substance_patents INT DEFAULT 0,
    formulation_patents INT DEFAULT 0,
    use_patents INT DEFAULT 0,
    earliest_expiry_date DATE,
    latest_expiry_date DATE,
    has_exclusivity BOOLEAN DEFAULT FALSE,
    exclusivity_expiry_date DATE,
    patent_cliff_risk VARCHAR(20),              -- High, Medium, Low
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patent_agg_drug ON patentaggregate(drug_id);

-- Comments:
-- 1. patent: Stores individual patents from Orange Book
-- 2. exclusivity: Regulatory exclusivity periods (often more important than patents)
-- 3. fda_precedent: Historical success rates by indication (calculated once, reused)
-- 4. approval_probability: Per-drug approval probability (recalculated when trial data changes)
-- 5. patentaggregate: Summary metrics for quick queries

-- Example exclusivity codes:
-- NCE = New Chemical Entity (5 years)
-- ODE = Orphan Drug Exclusivity (7 years)
-- PED = Pediatric Exclusivity (6 months)
-- NGE = New Formulation/Route/Combination (3 years)
