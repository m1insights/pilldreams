CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS Drug (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(255) NOT NULL,
  synonyms TEXT[],
  class VARCHAR(255),
  is_approved BOOLEAN DEFAULT false,
  first_approval_date DATE,
  drugbank_id VARCHAR(50),
  chembl_id VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_drug_name ON Drug(name);
CREATE INDEX IF NOT EXISTS idx_drug_chembl ON Drug(chembl_id);

CREATE TABLE IF NOT EXISTS Target (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  symbol VARCHAR(100) NOT NULL,
  description TEXT,
  uniprot_id VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_target_symbol ON Target(symbol);

CREATE TABLE IF NOT EXISTS DrugTarget (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  drug_id UUID REFERENCES Drug(id) ON DELETE CASCADE,
  target_id UUID REFERENCES Target(id) ON DELETE CASCADE,
  affinity_value FLOAT,
  affinity_unit VARCHAR(20),
  interaction_type VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_drugtarget_drug ON DrugTarget(drug_id);
CREATE INDEX IF NOT EXISTS idx_drugtarget_target ON DrugTarget(target_id);

CREATE TABLE IF NOT EXISTS Trial (
  nct_id VARCHAR(50) PRIMARY KEY,
  drug_id UUID REFERENCES Drug(id) ON DELETE CASCADE,
  phase VARCHAR(10),
  status VARCHAR(100),
  condition TEXT,
  sponsor_type VARCHAR(50),
  enrollment INTEGER,
  start_date DATE,
  primary_completion_date DATE,
  completion_date DATE,
  primary_endpoint TEXT,
  has_placebo_arm BOOLEAN,
  has_active_comparator BOOLEAN,
  is_randomized BOOLEAN,
  is_blinded BOOLEAN,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trial_drug ON Trial(drug_id);
CREATE INDEX IF NOT EXISTS idx_trial_phase ON Trial(phase);
CREATE INDEX IF NOT EXISTS idx_trial_status ON Trial(status);

CREATE TABLE IF NOT EXISTS SafetyAggregate (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  drug_id UUID REFERENCES Drug(id) ON DELETE CASCADE,
  meddra_term VARCHAR(255),
  case_count INTEGER,
  is_serious BOOLEAN,
  disproportionality_metric FLOAT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_safety_drug ON SafetyAggregate(drug_id);

CREATE TABLE IF NOT EXISTS EvidenceAggregate (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  drug_id UUID REFERENCES Drug(id) ON DELETE CASCADE,
  n_rcts INTEGER DEFAULT 0,
  n_meta_analyses INTEGER DEFAULT 0,
  median_pub_year INTEGER,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evidence_drug ON EvidenceAggregate(drug_id);

CREATE TABLE IF NOT EXISTS SentimentAggregate (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  drug_id UUID REFERENCES Drug(id) ON DELETE CASCADE,
  n_posts INTEGER DEFAULT 0,
  overall_sentiment FLOAT,
  mood_sentiment FLOAT,
  anxiety_sentiment FLOAT,
  weight_sentiment FLOAT,
  sexual_sentiment FLOAT,
  sleep_sentiment FLOAT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sentiment_drug ON SentimentAggregate(drug_id);

CREATE TABLE IF NOT EXISTS DrugScores (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  drug_id UUID REFERENCES Drug(id) ON DELETE CASCADE,
  trial_progress_score FLOAT,
  mechanism_score FLOAT,
  safety_score FLOAT,
  evidence_maturity_score FLOAT,
  sentiment_score FLOAT,
  approval_probability FLOAT,
  net_benefit_score FLOAT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scores_drug ON DrugScores(drug_id);
