# pilldreams Project Context

> **Project Directory**: `/Users/mananshah/Dev/pilldreams/`

---

## Project Overview

**pilldreams** is a Streamlit web application that provides comprehensive drug intelligence for retail biotech investors, PharmD/MD students, clinicians/pharmacists, and advanced patient/advocacy users.

### Core Features

Users type in a drug name and instantly see:
- **Approval Probability** (for drugs still in trials)
- **Mechanism of Action** (targets, receptors, chemical structure)
- **Trial Progress** (phases, statuses, timelines)
- **Safety Signals** (FDA adverse events)
- **Evidence Strength** (RCTs, meta-analyses)
- **Real-World Sentiment** (Reddit analysis - optional)
- **Composite Drug Score** (benefit vs risk vs evidence)
- **Embedded AI Chat** (explains the drug using app data as context)

---

## Tech Stack

- **Frontend/UI**: Streamlit
- **Backend Logic**: Python modules + MCP-based agents
- **Data Storage**: Supabase (PostgreSQL) - all backend operations
- **Cache**: Supabase caching + local session cache
- **Data Ingestion**: Scheduled Python scripts or manual triggers
- **Agent Architecture**: Code-execution MCP pattern (progressive disclosure, on-demand tool loading)

### Key Dependencies

```
streamlit
supabase-py
rdkit
stmol or py3Dmol
plotly or altair
requests or httpx
pandas
numpy
anthropic (Claude SDK)
```

### MCP Servers Available

- **Playwright MCP** - Web scraping, browser automation
- **Context7 MCP** - Library documentation lookup
- **Supabase MCP** - Database operations (queries, inserts, updates)

---

## Project Structure

```
/pilldreams
├── app/                    # Streamlit UI
│   ├── main.py            # Main app entry point
│   ├── tabs/              # UI tab components
│   │   ├── overview.py
│   │   ├── pharmacology.py
│   │   ├── trials.py
│   │   ├── safety.py
│   │   └── ai_chat.py
│   └── components/        # Reusable UI components
├── agents/                # MCP-based specialized agents
│   ├── orchestrator/      # Main orchestrator agent
│   │   ├── agent.py      # Orchestrator logic
│   │   └── context/      # Cached agent context
│   ├── playwright_agent/  # Web scraping agent
│   │   ├── agent.py
│   │   ├── skills/       # Reusable scraping skills
│   │   └── servers/      # MCP tool wrappers
│   │       └── playwright/
│   ├── supabase_agent/    # Database operations agent
│   │   ├── agent.py
│   │   ├── skills/       # Reusable DB queries
│   │   └── servers/      # MCP tool wrappers
│   │       └── supabase/
│   ├── context7_agent/    # Documentation lookup agent
│   │   ├── agent.py
│   │   ├── skills/       # Reusable doc lookups
│   │   └── servers/      # MCP tool wrappers
│   │       └── context7/
│   └── streamlit_agent/   # UI/visualization expert agent
│       ├── agent.py
│       ├── skills/        # Reusable UI patterns
│       └── knowledge/     # Streamlit docs, best practices
├── core/                  # Scoring engine, drug models
│   ├── scoring.py        # All scoring algorithms
│   ├── models.py         # Data models (Supabase)
│   └── supabase_client.py # Supabase connection
├── ingestion/            # Data collection scripts
│   ├── clinicaltrials.py
│   ├── drugbank_mechanism.py
│   ├── chembl_binding.py
│   ├── openfda_safety.py
│   ├── pubmed_evidence.py
│   └── reddit_sentiment.py
├── mcp_servers/          # MCP server tool definitions
│   ├── playwright/       # Playwright tool wrappers
│   ├── supabase/         # Supabase tool wrappers
│   └── context7/         # Context7 tool wrappers
├── workspace/            # Agent execution workspace
│   ├── cache/            # Cached results
│   └── temp/             # Temporary files
├── requirements.txt
└── CLAUDE.md            # This file
```

---

## MCP Agent Architecture (Code Execution Pattern)

> Based on [Anthropic's Code Execution with MCP Blog](https://www.anthropic.com/engineering/code-execution-with-mcp)

### Philosophy: Progressive Disclosure & On-Demand Tool Loading

Instead of loading all MCP tool definitions upfront (which can consume 100K+ tokens), we use a **code-execution pattern**:

1. **Present MCP servers as code APIs** - Tools are exposed as filesystem structure
2. **Load tools on-demand** - Agents explore filesystem to find relevant tools
3. **Process data in execution environment** - Filter/transform before passing to model
4. **Save reusable code as skills** - Build library of higher-level capabilities

### Token Efficiency Gains

**Before (Direct Tool Calling):**
- All tool definitions loaded upfront: ~150,000 tokens
- Intermediate results pass through context: +50,000 tokens per large doc
- Total: ~200,000+ tokens per session

**After (Code Execution Pattern):**
- On-demand tool loading: ~2,000 tokens
- Data filtered in execution environment: ~500 tokens for summary
- Total: ~2,500 tokens per session
- **Savings: 98.7%**

---

### Agent Roles & Responsibilities

#### 1. **Orchestrator Agent** (`agents/orchestrator/`)

**Role:** Main coordinator that routes tasks to specialized agents

**Responsibilities:**
- Receives user requests from Streamlit UI
- Classifies task type (scraping, database query, visualization, documentation lookup)
- Routes to appropriate specialist agent(s)
- Aggregates results and returns to UI
- Maintains session state and caching

**MCP Tools:** None directly (delegates to specialists)

**Example Flow:**
```python
# User asks: "Get trial data for metformin and visualize phase distribution"
orchestrator.classify_task(query)
# → Task type: [database_query, visualization]

# Delegate to specialists
trial_data = await supabase_agent.get_trials(drug="metformin")
chart = await streamlit_agent.create_phase_chart(trial_data)

return {"data": trial_data, "visualization": chart}
```

---

#### 2. **Playwright Agent** (`agents/playwright_agent/`)

**Role:** Web scraping specialist for DrugBank, Reddit, etc.

**Responsibilities:**
- Navigate to DrugBank pages and extract mechanism data
- Scrape Reddit posts/comments for sentiment analysis
- Handle pagination, authentication, dynamic content
- Save scraped data to workspace for processing
- Build reusable scraping skills

**MCP Tools:**
- `mcp__playwright__browser_navigate`
- `mcp__playwright__browser_snapshot`
- `mcp__playwright__browser_click`
- `mcp__playwright__browser_evaluate`

**Code Execution Pattern:**
```typescript
// agents/playwright_agent/servers/playwright/navigate.ts
import { callMCPTool } from "../../../client.js";

export async function navigate(url: string) {
  return callMCPTool('mcp__playwright__browser_navigate', { url });
}

// agents/playwright_agent/skills/scrape-drugbank.ts
import * as playwright from '../servers/playwright';

export async function scrapeDrugBankMechanism(drugName: string) {
  await playwright.navigate(`https://go.drugbank.com/drugs/${drugName}`);
  const snapshot = await playwright.snapshot();

  // Extract mechanism text (filter in execution environment)
  const mechanism = snapshot.find(el => el.role === 'region' &&
    el.name.includes('Mechanism of Action')).text;

  // Only return summary, not full page
  return { drug: drugName, mechanism: mechanism.slice(0, 500) };
}
```

**Saved Skills:**
- `scrape-drugbank.ts` - Extract mechanism, targets, class
- `scrape-reddit-sentiment.ts` - Get posts for drug name
- `extract-table-data.ts` - Parse HTML tables into JSON

---

#### 3. **Supabase Agent** (`agents/supabase_agent/`)

**Role:** Database operations specialist

**Responsibilities:**
- Query Supabase for drug data, trials, scores, etc.
- Insert/update records from ingestion scripts
- Aggregate data for scoring engine
- Filter and transform query results before returning
- Build reusable query skills

**MCP Tools:**
- `mcp__supabase__query` (assumed - check your Supabase MCP docs)
- `mcp__supabase__insert`
- `mcp__supabase__update`
- `mcp__supabase__delete`

**Code Execution Pattern:**
```typescript
// agents/supabase_agent/servers/supabase/query.ts
import { callMCPTool } from "../../../client.js";

export async function query(table: string, filters: object) {
  return callMCPTool('mcp__supabase__query', { table, filters });
}

// agents/supabase_agent/skills/get-drug-trials.ts
import * as supabase from '../servers/supabase';

export async function getDrugTrials(drugName: string) {
  // Get drug ID first
  const drug = await supabase.query('Drug', { name: drugName });

  // Get all trials (potentially 1000+ rows)
  const trials = await supabase.query('Trial', { drug_id: drug[0].id });

  // Filter in execution environment (not in model context)
  const activeTrials = trials.filter(t =>
    ['Recruiting', 'Active, not recruiting', 'Enrolling'].includes(t.status)
  );

  // Return summary stats, not all rows
  return {
    total_trials: trials.length,
    active_trials: activeTrials.length,
    phases: activeTrials.reduce((acc, t) => {
      acc[t.phase] = (acc[t.phase] || 0) + 1;
      return acc;
    }, {}),
    sample_trials: activeTrials.slice(0, 5) // Only first 5 for review
  };
}
```

**Saved Skills:**
- `get-drug-trials.ts` - Fetch and summarize trials
- `get-safety-data.ts` - Aggregate adverse events
- `get-drug-scores.ts` - Fetch all scores for drug
- `insert-trial-batch.ts` - Bulk insert trials from ingestion

---

#### 4. **Context7 Agent** (`agents/context7_agent/`)

**Role:** Documentation lookup specialist

**Responsibilities:**
- Fetch up-to-date library docs (Streamlit, Plotly, RDKit, etc.)
- Provide code examples for UI components
- Answer technical questions about dependencies
- Cache frequently-accessed docs

**MCP Tools:**
- `mcp__context7__resolve-library-id`
- `mcp__context7__get-library-docs`

**Code Execution Pattern:**
```typescript
// agents/context7_agent/servers/context7/get-docs.ts
import { callMCPTool } from "../../../client.js";

export async function getLibraryDocs(libraryId: string, topic?: string) {
  return callMCPTool('mcp__context7__get-library-docs', {
    context7CompatibleLibraryID: libraryId,
    topic
  });
}

// agents/context7_agent/skills/streamlit-chart-help.ts
import * as context7 from '../servers/context7';

export async function getStreamlitChartExample(chartType: string) {
  const docs = await context7.getLibraryDocs('/streamlit/streamlit', chartType);

  // Extract only code examples (filter out prose)
  const examples = docs.filter(d => d.type === 'code_snippet');

  return {
    chart_type: chartType,
    examples: examples.slice(0, 3), // Top 3 examples
    doc_link: docs[0].url
  };
}
```

**Saved Skills:**
- `streamlit-chart-help.ts` - Get chart examples
- `rdkit-structure-help.ts` - Get RDKit structure drawing examples
- `plotly-timeline-help.ts` - Get Plotly timeline examples

---

#### 5. **Streamlit Agent** (`agents/streamlit_agent/`)

**Role:** UI/visualization expert and data science specialist

**Responsibilities:**
- Create Streamlit components (charts, tables, metrics)
- Design data visualizations (Plotly, Altair)
- Implement best practices for Streamlit apps
- Optimize performance (caching, lazy loading)
- Call other MCP agents when needed (e.g., Context7 for docs)

**MCP Tools:**
- Can call Context7 agent for documentation
- Can call Supabase agent for data queries

**Knowledge Base:**
- Streamlit documentation (cached in `knowledge/`)
- Data visualization best practices
- Color palettes, layout patterns
- Performance optimization techniques

**Example Flow:**
```python
# User asks: "Create a radar chart for drug scores"
streamlit_agent.receive_task({
  "task": "create_radar_chart",
  "data": {"trial_score": 85, "safety_score": 72, ...}
})

# Streamlit agent checks knowledge base first
radar_code = streamlit_agent.knowledge.get("radar_chart_template")

# If not found, ask Context7 agent
if not radar_code:
  radar_code = await context7_agent.get_streamlit_example("radar chart")

# Generate code, save as skill
streamlit_agent.skills.save("radar-chart.py", radar_code)

return radar_chart_component
```

**Saved Skills:**
- `radar-chart.py` - Create radar/spider chart
- `trial-timeline.py` - Create trial timeline visualization
- `metric-cards.py` - Create metric card grid
- `ae-bar-chart.py` - Create adverse event bar chart

---

### Agent Communication Protocol

**1. Orchestrator → Specialist:**
```python
{
  "task_id": "uuid",
  "agent": "supabase_agent",
  "action": "get_drug_trials",
  "params": {"drug_name": "metformin"},
  "context": "User wants to see trial phase distribution"
}
```

**2. Specialist → Orchestrator:**
```python
{
  "task_id": "uuid",
  "status": "success",
  "result": {
    "total_trials": 1247,
    "active_trials": 89,
    "phases": {"I": 12, "II": 34, "III": 43},
    "sample_trials": [...]
  },
  "tokens_used": 2341,
  "execution_time_ms": 456
}
```

---

### Context Management & Caching

**Agent Context Cache** (`agents/{agent}/context/`)

Each agent maintains a cache to avoid re-discovering tools:

```json
// agents/playwright_agent/context/tools.json
{
  "last_updated": "2025-11-21T19:00:00Z",
  "available_tools": [
    {
      "name": "navigate",
      "path": "./servers/playwright/navigate.ts",
      "description": "Navigate to URL",
      "params": ["url"]
    },
    {
      "name": "snapshot",
      "path": "./servers/playwright/snapshot.ts",
      "description": "Capture page snapshot",
      "params": []
    }
  ]
}
```

**Workspace Cache** (`workspace/cache/`)

Stores frequently-accessed data to avoid redundant API calls:

```
workspace/cache/
├── drugbank_metformin.json      # DrugBank page data
├── trials_metformin.json        # ClinicalTrials.gov data
└── reddit_metformin_2025-11.json # Reddit sentiment data
```

---

### Skills Library

Each agent builds a library of reusable code over time:

**Example: Playwright Agent Skill**
```typescript
// agents/playwright_agent/skills/scrape-drugbank.ts

/**
 * SKILL: scrape-drugbank
 *
 * Description: Extract mechanism, targets, and drug class from DrugBank
 * Input: drugName (string)
 * Output: { mechanism, targets[], class }
 * Last Updated: 2025-11-21
 */

import * as playwright from '../servers/playwright';

export async function scrapeDrugBank(drugName: string) {
  const url = `https://go.drugbank.com/drugs/${drugName}`;
  await playwright.navigate(url);

  const snapshot = await playwright.snapshot();

  // Extract mechanism (already filtered in execution environment)
  const mechanism = extractMechanism(snapshot);
  const targets = extractTargets(snapshot);
  const drugClass = extractClass(snapshot);

  return { drug: drugName, mechanism, targets, class: drugClass };
}

function extractMechanism(snapshot) {
  // ... implementation ...
}
```

---

### Error Handling & Retry Logic

Agents implement robust error handling:

```typescript
// agents/supabase_agent/agent.ts

async function executeTask(task) {
  const MAX_RETRIES = 3;
  let attempt = 0;

  while (attempt < MAX_RETRIES) {
    try {
      const result = await runSkill(task.action, task.params);
      return { status: 'success', result };
    } catch (error) {
      attempt++;

      if (error.code === 'RATE_LIMIT') {
        await sleep(exponentialBackoff(attempt));
      } else if (attempt === MAX_RETRIES) {
        return {
          status: 'error',
          error: error.message,
          fallback: await getFallbackData(task)
        };
      }
    }
  }
}
```

---

### Privacy & Security

**Sensitive Data Tokenization:**

```python
# Orchestrator automatically tokenizes PII before passing to agents
user_data = supabase_agent.get_user_profile(user_id)

# Tokenize email/phone before passing to model
tokenized = {
  "user_id": user_data["user_id"],
  "email": "[EMAIL_1]",
  "phone": "[PHONE_1]",
  "name": "[NAME_1]"
}

# Real data flows through MCP tools, but model only sees tokens
```

---

## Data Sources (V1)

### Direct APIs
1. **ClinicalTrials.gov** - Trial data, phases, status, endpoints
2. **ChEMBL API** - Binding affinity, target data
3. **PubMed E-utilities** - Evidence classification (RCTs, meta-analyses)
4. **OpenFDA** - Adverse events, safety signals

### Scraped / Custom
5. **DrugBank** - Mechanism of action, drug class (HTML or paid API)
6. **Reddit** - Real-world sentiment (limited scope, targeted drugs)

---

## Data Model

### Drug
- `id` (primary key)
- `name` (generic name)
- `synonyms` (brand names, aliases)
- `class` (drug class/category)
- `is_approved` (boolean)
- `first_approval_date`
- `drugbank_id`
- `chembl_id`

### Target
- `id` (primary key)
- `symbol` (gene symbol)
- `description`
- `uniprot_id`

### DrugTarget (junction table)
- `drug_id` (foreign key)
- `target_id` (foreign key)
- `affinity_value` (Ki, IC50, etc.)
- `interaction_type` (agonist, antagonist, etc.)

### Trial
- `nct_id` (primary key)
- `drug_id` (foreign key)
- `phase` (0, I, II, III, IV)
- `status` (recruiting, completed, terminated, etc.)
- `condition` (indication being studied)
- `sponsor_type` (industry, NIH, academic, etc.)
- `enrollment` (target or actual n)
- `start_date`
- `primary_completion_date`
- `completion_date`
- `primary_endpoint`
- `has_placebo_arm` (boolean)
- `has_active_comparator` (boolean)
- `is_randomized` (boolean)
- `is_blinded` (boolean)

### SafetyAggregate
- `drug_id` (foreign key)
- `meddra_term` (adverse event term)
- `case_count`
- `is_serious` (boolean)
- `disproportionality_metric` (PRR-like score)

### EvidenceAggregate
- `drug_id` (foreign key)
- `n_rcts` (number of randomized controlled trials)
- `n_meta_analyses`
- `median_pub_year`

### SentimentAggregate
- `drug_id` (foreign key)
- `n_posts` (Reddit post count)
- `overall_sentiment` (-1 to +1)
- `mood_sentiment`
- `anxiety_sentiment`
- `weight_sentiment`
- `sexual_sentiment`
- `sleep_sentiment`

### DrugScores
- `drug_id` (foreign key)
- `trial_progress_score` (0–100)
- `mechanism_score` (0–100)
- `safety_score` (0–100)
- `evidence_maturity_score` (0–100)
- `sentiment_score` (0–100)
- `approval_probability` (0–1, for pipeline drugs)
- `net_benefit_score` (0–100, for approved drugs)

---

## Scoring Engine (Config Rules)

Location: `/core/scoring.py`

### Trial Progress Score (0–100)
Based on:
- Highest phase reached
- Completed vs terminated trials
- Sponsor type (industry = higher quality)
- Enrollment size
- Time to primary completion

### Mechanism Score (0–100)
Based on:
- Mechanism class maturity (established vs novel)
- Number/type of targets
- Off-target promiscuity penalties
- Known risky receptors (e.g., hERG channel)

### Safety Score (0–100)
Based on:
- Serious adverse events (frequency)
- PRR-like disproportionality metric
- High-severity AE frequency

### Evidence Maturity Score (0–100)
Based on:
- Number of RCTs
- Number of meta-analyses
- Recency (median pub year)
- Replication quality

### Sentiment Score (0–100)
Based on:
- Overall sentiment (-1 to +1 scale)
- Dimension sentiment (mood, anxiety, weight, sexual, sleep)
- Penalties for strongly negative areas

### Approval Probability (0–1)
**For pipeline drugs:**
- 40% trial progress
- 20% mechanism
- 20% safety
- 20% evidence maturity

### Net Benefit Score (0–100)
**For approved drugs:**
- 40% evidence maturity
- 30% safety
- 20% mechanism
- 10% sentiment

---

## Streamlit UI Layout

### Sidebar
- Drug search (`st.text_input`)
- Filter by class or approval status
- Select drug from dropdown list (`st.selectbox`)

### Tab: Overview
- Header: drug name + class + approval status
- Metric cards:
  - Approval Probability or Net Benefit Score
  - Trial Progress Score
  - Safety Score
  - Evidence Score
  - Sentiment Score (if available)
- Radar/spider chart or grouped bar chart summarizing all scores

### Tab: Pharmacology
- 2D chemical structure (RDKit → `st.image`)
- 3D molecule viewer (STmol or py3Dmol)
- Targets table:
  - Receptor/target name
  - Affinity value
  - Interaction type
- Receptor contribution bar chart

### Tab: Trials & Evidence
- Timeline chart of trials (Plotly/Altair)
- Table of trials with key fields:
  - NCT ID
  - Phase
  - Status
  - Condition
  - Enrollment
  - Dates
- Evidence summary:
  - Number of RCTs
  - Number of meta-analyses
  - Median publication year
- Publications-per-year chart (optional)

### Tab: Safety & Sentiment
- Table of top adverse events:
  - MedDRA term
  - Case count
  - Seriousness
  - PRR category
- Adverse event bar chart
- Sentiment summary (if available)
- Sentiment dimension bar charts (mood, anxiety, weight, etc.)

### Tab: AI Chat
- Use Streamlit's built-in chat interface:
  - `st.chat_message`
  - `st.chat_input`
- Inject context from:
  - Mechanism summary
  - Scores
  - Major trials
  - Key safety AEs
- AI assistant answers questions like:
  - "Explain this drug's mechanism in plain language."
  - "How does this compare to Drug X?"
  - "What side effects matter most here?"

---

## Build Phases

### Phase 0 – Setup ✅
- [x] Create project directory
- [x] Create CLAUDE.md with full architecture spec
- [ ] Create project structure (agents/, mcp_servers/, workspace/, etc.)
- [ ] Create Streamlit skeleton
- [ ] Set up Supabase project and credentials
- [ ] Initialize agent scaffolding (5 agents)
- [ ] Create `requirements.txt`
- [ ] Set up MCP server tool wrappers (Playwright, Supabase, Context7)

### Phase 1 – Hardcoded Prototype
- [ ] Manually load 1–2 drugs into database
- [ ] Build all UI tabs with placeholder data
- [ ] Establish design patterns for visuals
- [ ] Create reusable component library

### Phase 2 – Core Ingestion + Real Data
- [ ] Implement ClinicalTrials.gov ingestion
- [ ] Implement DrugBank mechanism scraping
- [ ] Implement ChEMBL binding data
- [ ] Implement Trial Progress Score
- [ ] Implement Mechanism Score
- [ ] Replace placeholder UI with dynamic data

### Phase 3 – Safety & Evidence
- [ ] Add OpenFDA ingestion
- [ ] Create SafetyAggregate table
- [ ] Implement Safety Score
- [ ] Add PubMed E-utilities ingestion
- [ ] Create EvidenceAggregate table
- [ ] Implement Evidence Maturity Score
- [ ] Update Safety & Sentiment tab

### Phase 4 – Sentiment & AI Chat
- [ ] Limited Reddit sentiment scraping
- [ ] Implement sentiment analysis
- [ ] Add Sentiment Score
- [ ] Build AI chat interface
- [ ] Implement context injection for AI

### Phase 5 – Polish & Expansion
- [ ] Improve layout consistency (cards, spacing, colors)
- [ ] Add more drugs across multiple classes
- [ ] Create About/Methodology page
- [ ] Add export functionality (PDF reports, CSV data)
- [ ] Performance optimization
- [ ] Error handling and edge cases

---

## Data Ingestion Scripts

### Script: `ingestion/clinicaltrials.py`
- **Input**: Drug names
- **API**: ClinicalTrials.gov REST API
- **Output**: Populate/update `Trial` table
- **Normalization**: Phase, sponsor type, status
- **Frequency**: Weekly or on-demand

### Script: `ingestion/drugbank_mechanism.py`
- **Input**: Drug names
- **Source**: DrugBank HTML or API
- **Extract**: Mechanism text, drug class, targets/receptors
- **Output**: Populate `Drug`, `Target`, `DrugTarget` tables
- **Frequency**: Monthly or on-demand

### Script: `ingestion/chembl_binding.py`
- **Input**: ChEMBL ID
- **API**: ChEMBL REST API
- **Extract**: Binding assays, affinity values
- **Normalization**: Convert all affinities to standard units
- **Output**: Populate/update `DrugTarget` table
- **Frequency**: Monthly

### Script: `ingestion/openfda_safety.py`
- **Input**: Drug names
- **API**: OpenFDA Drug Adverse Events API
- **Aggregate**: By MedDRA term
- **Compute**: PRR-like disproportionality metric
- **Output**: Populate `SafetyAggregate` table
- **Frequency**: Monthly

### Script: `ingestion/pubmed_evidence.py`
- **Input**: Drug name + indication
- **API**: PubMed E-utilities
- **Classify**: Papers as RCT vs meta-analysis
- **Compute**: Median publication year
- **Output**: Populate `EvidenceAggregate` table
- **Frequency**: Quarterly

### Script: `ingestion/reddit_sentiment.py` (Optional V1)
- **Input**: Drug names
- **Source**: Reddit API or PRAW
- **Scrape**: Posts/comments mentioning drug
- **Analyze**: Sentiment per dimension
- **Aggregate**: Per drug
- **Output**: Populate `SentimentAggregate` table
- **Frequency**: Weekly

---

## Development Commands

### Run Streamlit App
```bash
cd /Users/mananshah/Dev/pilldreams
streamlit run app/main.py
```

### Run Ingestion Scripts
```bash
# Individual scripts
python ingestion/clinicaltrials.py --drug "metformin"
python ingestion/drugbank_mechanism.py --drug "metformin"
python ingestion/chembl_binding.py --chembl-id "CHEMBL1431"

# Batch ingestion
python ingestion/batch_ingest.py --drug-list drugs.txt
```

### Database Management (Supabase)
```bash
# Initialize Supabase tables (run migrations)
python core/supabase_client.py --init

# Seed database with sample data
python core/supabase_client.py --seed

# Query database via Supabase agent
python -c "from agents.supabase_agent import agent; agent.query('Drug', limit=10)"
```

---

## Design Principles

1. **Transparency**: Show data sources and scoring methodology clearly
2. **Evidence-Based**: Prioritize clinical trial data and peer-reviewed evidence
3. **User-Friendly**: Clear visualizations, minimal jargon, helpful tooltips
4. **Fast**: Cache data, optimize queries, lazy-load visualizations
5. **Modular**: Separate ingestion, scoring, and UI logic
6. **Maintainable**: Well-documented code, consistent patterns

---

## Key Decisions

### Why Supabase?
- PostgreSQL-based (production-ready from day 1)
- Built-in REST API and real-time subscriptions
- Row-level security and authentication
- Generous free tier (500MB database, 2GB file storage)
- Easy to query via Python SDK and MCP
- Automatic backups and migrations
- Can scale to millions of rows without refactoring

### Why Streamlit?
- Rapid prototyping
- Built-in caching and state management
- Great for data-heavy applications
- Easy deployment (Streamlit Cloud, Render, etc.)

### Why Config-Based Scoring?
- Transparency: users can see how scores are calculated
- Flexibility: easy to adjust weights and rules
- Reproducibility: same inputs → same outputs
- Testability: can validate scoring logic independently

### Why MCP Agent Architecture?
- **Token efficiency**: 98.7% reduction via progressive disclosure
- **Modularity**: Each agent has single responsibility
- **Reusability**: Skills library grows over time
- **Scalability**: Add new agents without refactoring
- **Debuggability**: Trace execution through agent logs

### API Rate Limits
- **ClinicalTrials.gov**: No strict limits, but be respectful
- **ChEMBL**: Rate limited, implement caching
- **PubMed**: 3 requests/second without API key, 10/sec with key
- **OpenFDA**: 240 requests/minute (40/second)

---

## Future Enhancements (Post-V1)

- **Comparative Analysis**: Side-by-side drug comparisons
- **Portfolio Tracking**: Save and monitor multiple drugs
- **Alerts**: Notify on new trial results or FDA updates
- **Export Reports**: PDF/CSV downloads
- **Advanced Search**: Filter by mechanism, indication, phase
- **API Access**: Provide REST API for power users
- **Mobile Optimization**: Responsive design for mobile browsers
- **User Accounts**: Save preferences and watchlists

---

## Notes

- This app is for **informational purposes only** and should not be used as medical advice
- Always cite data sources clearly
- Respect API rate limits and terms of service
- Consider adding disclaimer about investment risks
- Ensure HIPAA compliance if handling patient data (future feature)

---

## Agent Implementation Guide

### Creating a New Agent

Each agent follows this template structure:

```
agents/{agent_name}/
├── agent.py              # Main agent logic
├── config.json           # Agent configuration
├── servers/              # MCP tool wrappers
│   └── {mcp_name}/
│       ├── tool1.ts      # Tool wrapper
│       └── tool2.ts
├── skills/               # Reusable functions
│   ├── skill1.ts
│   └── SKILL.md          # Skills documentation
├── context/              # Cached context
│   └── tools.json        # Discovered tools cache
└── README.md             # Agent documentation
```

### Agent Configuration Template

```json
// agents/{agent_name}/config.json
{
  "name": "playwright_agent",
  "role": "Web scraping specialist",
  "mcp_servers": ["playwright"],
  "skills_path": "./skills",
  "context_cache_ttl": 3600,
  "max_retries": 3,
  "timeout_ms": 30000
}
```

### Agent Base Class

```python
# agents/base_agent.py

from abc import ABC, abstractmethod
from typing import Dict, Any
import json

class BaseAgent(ABC):
    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.config = json.load(f)

        self.name = self.config['name']
        self.role = self.config['role']
        self.skills = self.load_skills()
        self.context_cache = self.load_context_cache()

    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task and return result"""
        pass

    def load_skills(self):
        """Load available skills from skills/ directory"""
        # Implementation details...
        pass

    def load_context_cache(self):
        """Load cached MCP tool definitions"""
        # Implementation details...
        pass

    def save_skill(self, name: str, code: str):
        """Save new skill to skills/ directory"""
        # Implementation details...
        pass
```

### MCP Tool Wrapper Template

```typescript
// agents/{agent}/servers/{mcp}/tool_name.ts
import { callMCPTool } from "../../../client.js";

interface ToolInput {
  param1: string;
  param2?: number;
}

interface ToolOutput {
  result: any;
}

/**
 * Tool: tool_name
 * Description: What this tool does
 */
export async function toolName(input: ToolInput): Promise<ToolOutput> {
  return callMCPTool<ToolOutput>('mcp__server__tool_name', {
    param1: input.param1,
    param2: input.param2
  });
}
```

### Skill Template

```typescript
// agents/{agent}/skills/skill_name.ts

/**
 * SKILL: skill-name
 *
 * Description: High-level description of what this skill does
 * Input: { param1: type, param2: type }
 * Output: { result: type }
 * Dependencies: List of MCP tools used
 * Last Updated: YYYY-MM-DD
 * Performance: ~X seconds, ~Y tokens
 */

import * as mcpServer from '../servers/{mcp}';

export async function skillName(input: SkillInput): Promise<SkillOutput> {
  // 1. Call MCP tools
  const rawData = await mcpServer.getTool(input.param1);

  // 2. Filter/transform in execution environment
  const filtered = rawData.filter(item => item.isRelevant);

  // 3. Return summary (not full data)
  return {
    summary: filtered.length,
    top_items: filtered.slice(0, 5),
    metadata: { timestamp: Date.now() }
  };
}
```

---

## Supabase Schema

### Tables

**Drug**
```sql
CREATE TABLE Drug (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(255) NOT NULL,
  synonyms TEXT[], -- Array of alternative names
  class VARCHAR(255),
  is_approved BOOLEAN DEFAULT false,
  first_approval_date DATE,
  drugbank_id VARCHAR(50),
  chembl_id VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_drug_name ON Drug(name);
CREATE INDEX idx_drug_chembl ON Drug(chembl_id);
```

**Target**
```sql
CREATE TABLE Target (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  symbol VARCHAR(100) NOT NULL,
  description TEXT,
  uniprot_id VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_target_symbol ON Target(symbol);
```

**DrugTarget**
```sql
CREATE TABLE DrugTarget (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  drug_id UUID REFERENCES Drug(id) ON DELETE CASCADE,
  target_id UUID REFERENCES Target(id) ON DELETE CASCADE,
  affinity_value FLOAT,
  affinity_unit VARCHAR(20), -- 'nM', 'uM', 'Ki', 'IC50'
  interaction_type VARCHAR(50), -- 'agonist', 'antagonist', etc.
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_drugtarget_drug ON DrugTarget(drug_id);
CREATE INDEX idx_drugtarget_target ON DrugTarget(target_id);
```

**Trial**
```sql
CREATE TABLE Trial (
  nct_id VARCHAR(50) PRIMARY KEY,
  drug_id UUID REFERENCES Drug(id) ON DELETE CASCADE,
  phase VARCHAR(10), -- '0', 'I', 'II', 'III', 'IV'
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

CREATE INDEX idx_trial_drug ON Trial(drug_id);
CREATE INDEX idx_trial_phase ON Trial(phase);
CREATE INDEX idx_trial_status ON Trial(status);
```

**SafetyAggregate**
```sql
CREATE TABLE SafetyAggregate (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  drug_id UUID REFERENCES Drug(id) ON DELETE CASCADE,
  meddra_term VARCHAR(255),
  case_count INTEGER,
  is_serious BOOLEAN,
  disproportionality_metric FLOAT, -- PRR-like score
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_safety_drug ON SafetyAggregate(drug_id);
```

**EvidenceAggregate**
```sql
CREATE TABLE EvidenceAggregate (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  drug_id UUID REFERENCES Drug(id) ON DELETE CASCADE,
  n_rcts INTEGER DEFAULT 0,
  n_meta_analyses INTEGER DEFAULT 0,
  median_pub_year INTEGER,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_evidence_drug ON EvidenceAggregate(drug_id);
```

**SentimentAggregate**
```sql
CREATE TABLE SentimentAggregate (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  drug_id UUID REFERENCES Drug(id) ON DELETE CASCADE,
  n_posts INTEGER DEFAULT 0,
  overall_sentiment FLOAT, -- -1 to +1
  mood_sentiment FLOAT,
  anxiety_sentiment FLOAT,
  weight_sentiment FLOAT,
  sexual_sentiment FLOAT,
  sleep_sentiment FLOAT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sentiment_drug ON SentimentAggregate(drug_id);
```

**DrugScores**
```sql
CREATE TABLE DrugScores (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  drug_id UUID REFERENCES Drug(id) ON DELETE CASCADE,
  trial_progress_score FLOAT, -- 0-100
  mechanism_score FLOAT, -- 0-100
  safety_score FLOAT, -- 0-100
  evidence_maturity_score FLOAT, -- 0-100
  sentiment_score FLOAT, -- 0-100
  approval_probability FLOAT, -- 0-1 (for pipeline drugs)
  net_benefit_score FLOAT, -- 0-100 (for approved drugs)
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_scores_drug ON DrugScores(drug_id);
```

---

## Contact & Support

**Developer**: Manan Shah
**Project Start**: November 2025
**Current Phase**: Phase 0 (Setup)
