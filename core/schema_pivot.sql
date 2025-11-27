-- Drop existing tables to start fresh
DROP TABLE IF EXISTS drug_id_map CASCADE;
DROP TABLE IF EXISTS drug_targets CASCADE;
DROP TABLE IF EXISTS drug_indications CASCADE;
DROP TABLE IF EXISTS drugs CASCADE;

-- Core drugs table
CREATE TABLE drugs (
  id SERIAL PRIMARY KEY,
  ot_drug_id TEXT UNIQUE NOT NULL,
  chembl_id TEXT,
  name TEXT,
  pref_name TEXT,
  drug_type TEXT,
  max_phase TEXT,
  pubmed_count INT DEFAULT 0,
  openfda_ae_count INT DEFAULT 0,
  serious_ae_ratio FLOAT,
  is_gold_set BOOLEAN DEFAULT FALSE
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Drug-disease links
CREATE TABLE drug_indications (
  id SERIAL PRIMARY KEY,
  drug_id INT REFERENCES drugs(id) ON DELETE CASCADE,
  efo_disease_id TEXT NOT NULL,
  disease_name TEXT,
  phase TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Drug-target-mechanism links
CREATE TABLE drug_targets (
  id SERIAL PRIMARY KEY,
  drug_id INT REFERENCES drugs(id) ON DELETE CASCADE,
  ot_target_id TEXT NOT NULL,
  ensembl_id TEXT,
  uniprot_id TEXT,
  approved_symbol TEXT,
  mechanism_of_action TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Store external ID mappings
CREATE TABLE drug_id_map (
  id SERIAL PRIMARY KEY,
  drug_id INT REFERENCES drugs(id) ON DELETE CASCADE,
  id_type TEXT, -- 'chembl', 'drugbank', etc.
  external_id TEXT,
  UNIQUE(drug_id, id_type, external_id)
);

-- Indexes for common queries
CREATE INDEX idx_drugs_ot_drug_id ON drugs(ot_drug_id);
CREATE INDEX idx_drugs_gold_set ON drugs(is_gold_set);
CREATE INDEX idx_drug_indications_disease ON drug_indications(efo_disease_id);
CREATE INDEX idx_drug_targets_target ON drug_targets(ot_target_id);

-- Pipeline Assets (Experimental/Early Phase)
CREATE TABLE pipeline_assets (
  id SERIAL PRIMARY KEY,
  ot_drug_id TEXT UNIQUE NOT NULL,
  name TEXT,
  phase TEXT,
  target_evidence_score FLOAT, -- Average OT association score
  relative_score FLOAT,        -- Calculated relative score (Legacy V1)
  bio_score FLOAT,             -- 0-100 Biological Rationale
  chem_score FLOAT,            -- 0-100 Chemistry Quality
  tractability_score FLOAT,    -- 0-100 Target Druggability
  total_score FLOAT,           -- 0-100 Weighted Total
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE pipeline_asset_targets (
  id SERIAL PRIMARY KEY,
  pipeline_asset_id INT REFERENCES pipeline_assets(id) ON DELETE CASCADE,
  ot_target_id TEXT NOT NULL,
  approved_symbol TEXT,
  mechanism_of_action TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE pipeline_asset_indications (
  id SERIAL PRIMARY KEY,
  pipeline_asset_id INT REFERENCES pipeline_assets(id) ON DELETE CASCADE,
  efo_disease_id TEXT NOT NULL,
  disease_name TEXT,
  phase TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pipeline_assets_ot_id ON pipeline_assets(ot_drug_id);

-- ChEMBL Metrics (Chemistry Quality Layer)
CREATE TABLE chembl_metrics (
  id SERIAL PRIMARY KEY,
  drug_id INT REFERENCES drugs(id) ON DELETE CASCADE,
  pipeline_asset_id INT REFERENCES pipeline_assets(id) ON DELETE CASCADE, -- Link to either
  p_act_median FLOAT,
  p_act_best FLOAT,
  p_off_best FLOAT,
  delta_p FLOAT,
  n_activities_primary INT,
  n_activities_total INT,
  chem_score FLOAT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chembl_metrics_drug ON chembl_metrics(drug_id);
CREATE INDEX idx_chembl_metrics_pipeline ON chembl_metrics(pipeline_asset_id);

-- Target Biology Metrics (Tractability Layer)
CREATE TABLE target_biology_metrics (
  id SERIAL PRIMARY KEY,
  ot_target_id TEXT UNIQUE NOT NULL,
  small_molecule_tractability_bucket INT,
  antibody_tractability_bucket INT,
  tractability_score FLOAT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_target_biology_ot_id ON target_biology_metrics(ot_target_id);
