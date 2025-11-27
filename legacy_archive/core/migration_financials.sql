-- Add snapshot fields to company table
ALTER TABLE company ADD COLUMN IF NOT EXISTS cash_balance NUMERIC;
ALTER TABLE company ADD COLUMN IF NOT EXISTS monthly_burn_rate NUMERIC;
ALTER TABLE company ADD COLUMN IF NOT EXISTS net_income NUMERIC;
ALTER TABLE company ADD COLUMN IF NOT EXISTS total_revenue NUMERIC;
ALTER TABLE company ADD COLUMN IF NOT EXISTS last_price NUMERIC;
ALTER TABLE company ADD COLUMN IF NOT EXISTS last_volume BIGINT;
ALTER TABLE company ADD COLUMN IF NOT EXISTS last_updated_financials TIMESTAMP WITH TIME ZONE;

-- Create table for historical price data
CREATE TABLE IF NOT EXISTS stock_price_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES company(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(company_id, date)
);

-- Index for fast retrieval by company and date
CREATE INDEX IF NOT EXISTS idx_stock_price_company_date ON stock_price_history(company_id, date);
