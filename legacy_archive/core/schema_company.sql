-- Company-Centric Schema Migration
-- Adds support for tracking publicly traded biopharma companies and their pipelines

-- Company Table: Publicly traded biopharma companies
CREATE TABLE IF NOT EXISTS company (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  ticker VARCHAR(10) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  exchange VARCHAR(20) DEFAULT 'NASDAQ',
  market_category VARCHAR(50),  -- 'Q' = Global Select, 'G' = Global, 'S' = Capital
  financial_status VARCHAR(10),  -- 'N' = Normal, 'D' = Deficient
  cik VARCHAR(20),  -- SEC CIK number
  is_nbi_member BOOLEAN DEFAULT false,  -- NASDAQ Biotechnology Index member
  market_cap BIGINT,  -- Latest market cap in USD
  employee_count INTEGER,
  founded_year INTEGER,
  headquarters VARCHAR(255),
  website VARCHAR(255),
  description TEXT,
  therapeutic_focus TEXT[],  -- e.g., ['Oncology', 'CNS', 'Immunology']
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_company_ticker ON company(ticker);
CREATE INDEX IF NOT EXISTS idx_company_name ON company(name);
CREATE INDEX IF NOT EXISTS idx_company_nbi ON company(is_nbi_member);

-- Company-Drug Junction Table: Links companies to their pipeline drugs
CREATE TABLE IF NOT EXISTS company_drug (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID REFERENCES company(id) ON DELETE CASCADE,
  drug_id UUID REFERENCES drug(id) ON DELETE CASCADE,
  development_stage VARCHAR(50),  -- 'Preclinical', 'Phase 1', 'Phase 2', 'Phase 3', 'Approved', 'Discontinued'
  is_lead_program BOOLEAN DEFAULT false,  -- Is this a key pipeline asset?
  acquisition_date DATE,  -- If drug was acquired
  partner_company_id UUID REFERENCES company(id),  -- For partnership/licensing deals
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(company_id, drug_id)
);

CREATE INDEX IF NOT EXISTS idx_company_drug_company ON company_drug(company_id);
CREATE INDEX IF NOT EXISTS idx_company_drug_drug ON company_drug(drug_id);
CREATE INDEX IF NOT EXISTS idx_company_drug_stage ON company_drug(development_stage);

-- Catalyst Table: Upcoming events that could move stock price
CREATE TABLE IF NOT EXISTS catalyst (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID REFERENCES company(id) ON DELETE CASCADE,
  drug_id UUID REFERENCES drug(id) ON DELETE SET NULL,
  trial_id VARCHAR(50) REFERENCES trial(nct_id) ON DELETE SET NULL,
  catalyst_type VARCHAR(50) NOT NULL,  -- 'Data Readout', 'FDA Decision', 'Conference Presentation', 'Earnings', 'PDUFA'
  expected_date DATE,
  expected_quarter VARCHAR(10),  -- 'Q1 2025', 'H2 2025'
  description TEXT,
  source_url TEXT,
  confidence VARCHAR(20),  -- 'Confirmed', 'Estimated', 'Speculative'
  is_binary_event BOOLEAN DEFAULT false,  -- Does this event have pass/fail outcome?
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_catalyst_company ON catalyst(company_id);
CREATE INDEX IF NOT EXISTS idx_catalyst_drug ON catalyst(drug_id);
CREATE INDEX IF NOT EXISTS idx_catalyst_date ON catalyst(expected_date);
CREATE INDEX IF NOT EXISTS idx_catalyst_type ON catalyst(catalyst_type);

-- Stock Price History (optional, for charts)
CREATE TABLE IF NOT EXISTS stock_price (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID REFERENCES company(id) ON DELETE CASCADE,
  price_date DATE NOT NULL,
  open_price DECIMAL(10, 4),
  high_price DECIMAL(10, 4),
  low_price DECIMAL(10, 4),
  close_price DECIMAL(10, 4),
  volume BIGINT,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(company_id, price_date)
);

CREATE INDEX IF NOT EXISTS idx_stock_price_company ON stock_price(company_id);
CREATE INDEX IF NOT EXISTS idx_stock_price_date ON stock_price(price_date);

-- Company Financials (quarterly data)
CREATE TABLE IF NOT EXISTS company_financials (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID REFERENCES company(id) ON DELETE CASCADE,
  fiscal_quarter VARCHAR(10) NOT NULL,  -- 'Q1 2025'
  fiscal_year INTEGER NOT NULL,
  revenue BIGINT,  -- In thousands USD
  net_income BIGINT,  -- In thousands USD
  cash_and_equivalents BIGINT,  -- In thousands USD
  total_debt BIGINT,  -- In thousands USD
  r_and_d_expense BIGINT,  -- In thousands USD
  runway_months INTEGER,  -- Calculated: cash / monthly burn rate
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(company_id, fiscal_quarter, fiscal_year)
);

CREATE INDEX IF NOT EXISTS idx_financials_company ON company_financials(company_id);

-- Add company_id foreign key to existing drug table
ALTER TABLE drug ADD COLUMN IF NOT EXISTS sponsor_company_id UUID REFERENCES company(id);
CREATE INDEX IF NOT EXISTS idx_drug_sponsor ON drug(sponsor_company_id);

-- Add trial_id foreign key from trial to company (for sponsor)
ALTER TABLE trial ADD COLUMN IF NOT EXISTS sponsor_company_id UUID REFERENCES company(id);
CREATE INDEX IF NOT EXISTS idx_trial_sponsor_company ON trial(sponsor_company_id);
