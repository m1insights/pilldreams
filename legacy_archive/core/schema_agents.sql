-- Agent Logs
CREATE TABLE IF NOT EXISTS AgentLog (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(50) NOT NULL,
    log_level VARCHAR(20) NOT NULL, -- INFO, WARNING, ERROR
    message TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agentlog_agent ON AgentLog(agent_name);
CREATE INDEX IF NOT EXISTS idx_agentlog_created ON AgentLog(created_at);

-- Scientific Summaries (CSO Agent)
CREATE TABLE IF NOT EXISTS ScientificSummary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drug_id UUID REFERENCES Drug(id) ON DELETE CASCADE,
    mechanism_of_action TEXT,
    molecular_weight FLOAT,
    target_interaction_summary TEXT,
    science_score FLOAT, -- 0-100
    validation_warnings TEXT[],
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scisum_drug ON ScientificSummary(drug_id);

-- Investment Insights (Portfolio Manager Agent)
CREATE TABLE IF NOT EXISTS InvestmentInsight (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES Company(id) ON DELETE CASCADE,
    insight_type VARCHAR(50), -- RISK, OPPORTUNITY, CATALYST
    severity VARCHAR(20), -- LOW, MEDIUM, HIGH, CRITICAL
    title VARCHAR(255),
    description TEXT,
    supporting_data JSONB, -- e.g. {"cash_runway_months": 3, "next_readout_date": "2025-11-01"}
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_invest_company ON InvestmentInsight(company_id);
CREATE INDEX IF NOT EXISTS idx_invest_type ON InvestmentInsight(insight_type);

-- News Events (News Hound Agent)
CREATE TABLE IF NOT EXISTS NewsEvent (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(512) NOT NULL,
    url TEXT,
    source VARCHAR(100),
    published_at TIMESTAMP,
    summary TEXT,
    sentiment_score FLOAT,
    related_company_ids UUID[], -- Array of Company UUIDs
    related_drug_ids UUID[], -- Array of Drug UUIDs
    event_type VARCHAR(50), -- CLINICAL_TRIAL, FDA, FINANCIAL, MERGER
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_news_published ON NewsEvent(published_at);
