-- Company Intelligence Layer for Pilldreams
-- Creates tables for company-to-drug asset mapping

-- ============================================================
-- 1. Companies Table
-- ============================================================
CREATE TABLE IF NOT EXISTS epi_companies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  ticker TEXT,                -- Stock ticker (e.g., AGIO, BMY)
  exchange TEXT,              -- NYSE, NASDAQ, etc.
  market_cap BIGINT,          -- Market cap in USD
  sector TEXT DEFAULT 'Healthcare',
  industry TEXT DEFAULT 'Biotechnology',
  description TEXT,
  logo_url TEXT,
  website TEXT,
  headquarters TEXT,
  founded_year INT,
  employee_count INT,
  -- Epigenetics Focus
  epi_focus_score FLOAT,      -- 0-100: How focused on epigenetics
  is_pure_play_epi BOOLEAN DEFAULT FALSE,  -- Pure epigenetics company
  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for quick lookups
CREATE INDEX IF NOT EXISTS idx_epi_companies_ticker ON epi_companies(ticker);
CREATE INDEX IF NOT EXISTS idx_epi_companies_name ON epi_companies(name);
CREATE INDEX IF NOT EXISTS idx_epi_companies_market_cap ON epi_companies(market_cap DESC);

-- ============================================================
-- 2. Drug-Company Junction Table
-- ============================================================
-- A drug can be developed/marketed by multiple companies
CREATE TABLE IF NOT EXISTS epi_drug_companies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  drug_id UUID REFERENCES epi_drugs(id) ON DELETE CASCADE,
  company_id UUID REFERENCES epi_companies(id) ON DELETE CASCADE,
  role TEXT,                  -- 'originator', 'licensee', 'co-developer', 'marketer'
  is_primary BOOLEAN DEFAULT FALSE,  -- Primary company for this drug
  territory TEXT,             -- Geographic territory (e.g., 'US', 'EU', 'Global')
  deal_date DATE,             -- When the deal was made
  deal_value BIGINT,          -- Deal value in USD (if known)
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(drug_id, company_id, role)
);

CREATE INDEX IF NOT EXISTS idx_epi_drug_companies_drug ON epi_drug_companies(drug_id);
CREATE INDEX IF NOT EXISTS idx_epi_drug_companies_company ON epi_drug_companies(company_id);

-- ============================================================
-- 3. Editing Asset-Company Junction (for epi_editing_assets)
-- ============================================================
CREATE TABLE IF NOT EXISTS epi_editing_asset_companies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  editing_asset_id UUID REFERENCES epi_editing_assets(id) ON DELETE CASCADE,
  company_id UUID REFERENCES epi_companies(id) ON DELETE CASCADE,
  role TEXT DEFAULT 'originator',
  is_primary BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(editing_asset_id, company_id)
);

CREATE INDEX IF NOT EXISTS idx_epi_editing_asset_companies_asset ON epi_editing_asset_companies(editing_asset_id);
CREATE INDEX IF NOT EXISTS idx_epi_editing_asset_companies_company ON epi_editing_asset_companies(company_id);

-- ============================================================
-- 4. Company Pipeline Summary View
-- ============================================================
CREATE OR REPLACE VIEW v_epi_company_pipeline AS
SELECT
  c.id,
  c.name,
  c.ticker,
  c.market_cap,
  c.epi_focus_score,
  c.is_pure_play_epi,
  COUNT(DISTINCT dc.drug_id) as drug_count,
  COUNT(DISTINCT eac.editing_asset_id) as editing_asset_count,
  COUNT(DISTINCT dc.drug_id) + COUNT(DISTINCT eac.editing_asset_id) as total_asset_count,
  AVG(CASE WHEN dc.drug_id IS NOT NULL THEN
    (SELECT total_score FROM epi_scores WHERE drug_id = dc.drug_id LIMIT 1)
  END) as avg_drug_score
FROM epi_companies c
LEFT JOIN epi_drug_companies dc ON c.id = dc.company_id
LEFT JOIN epi_editing_asset_companies eac ON c.id = eac.company_id
GROUP BY c.id, c.name, c.ticker, c.market_cap, c.epi_focus_score, c.is_pure_play_epi;

-- ============================================================
-- 5. Company Drug Details View
-- ============================================================
CREATE OR REPLACE VIEW v_epi_company_drugs AS
SELECT
  c.id as company_id,
  c.name as company_name,
  c.ticker,
  d.id as drug_id,
  d.name as drug_name,
  d.fda_approved,
  dc.role,
  dc.is_primary,
  s.total_score,
  s.bio_score,
  s.chem_score,
  s.tractability_score
FROM epi_companies c
JOIN epi_drug_companies dc ON c.id = dc.company_id
JOIN epi_drugs d ON dc.drug_id = d.id
LEFT JOIN epi_scores s ON d.id = s.drug_id;
