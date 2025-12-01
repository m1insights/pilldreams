# pilldreams Project Context

> **Project Directory**: `/Users/mananshah/Dev/pilldreams/`
> **Last Updated**: 2025-11-30

---

## Strategic Direction (Pivot: Epigenetics Oncology Intelligence)

**Core Philosophy**: We provide a specialized intelligence platform for **Epigenetic Oncology**. We evaluate experimental assets targeting epigenetic mechanisms (e.g., HDAC, BET, EZH2) in cancer.

**Key Entities**:
1.  **Targets**: Epigenetic regulators (writers, readers, erasers).
2.  **Drugs**: Small molecules and biologics targeting these proteins.
3.  **Indications**: Oncology indications where these targets are relevant.

---

## The Intelligence Engine (Weighted Scoring)

We score every pipeline asset (0-100) based on three layers of evidence:

### 1. Biological Rationale (BioScore)
*   **Weight**: 50%
*   **Source**: Open Targets (Genetics, Somatic Mutations, Animal Models).
*   **Logic**: Does the target have strong biological validation for the disease?

### 2. Chemistry Quality (ChemScore)
*   **Weight**: 30%
*   **Source**: ChEMBL (Bioactivity Data).
*   **Metrics**:
    *   **Potency**: $pXC_{50}$ (Best on-target activity).
    *   **Selectivity**: $\Delta p$ (Difference vs. off-target).
    *   **Richness**: Number of confirming experiments.

### 3. Target Tractability (TractabilityScore)
*   **Weight**: 20%
*   **Source**: UniProt / Open Targets.
*   **Logic**: Is the target "druggable"? (Small Molecule Tractability Buckets).

**TotalScore Formula**:
$$ TotalScore = 0.5 \times Bio + 0.3 \times Chem + 0.2 \times Tract $$
*(With renormalization for missing data and floor caps for weak biology)*

---

## User Workflow: "Company-First" Watchlist

We shifted from a global explorer to a privacy-focused **Watchlist** model.

1.  **Search**: User searches for a company (e.g., "Vertex", "Lilly").
2.  **Dashboard**: User views the company's stock chart (TradingView) and description.
3.  **Follow**: User clicks "Follow" to add the company to their **Watchlist**.
4.  **Intelligence**: The system then reveals the **Scored Pipeline Assets** for that company.

---

## Tech Stack

*   **Backend**: FastAPI (`backend/main.py`)
*   **Database**: Supabase (PostgreSQL)
*   **Frontend**: Next.js (`frontend/`)
*   **AI Layer**: Google Gemini (`backend/ai/`)
*   **ETL**: Python Scripts (`backend/etl/`)
    *   `open_targets.py`: Disease & Drug ingestion.
    *   `chembl.py`: Chemistry data.
    *   `companies.py`: Company data via `yfinance`.
    *   `clinicaltrials.py`: CT.gov API v2 client.
    *   `ctgov_pipeline.py`: Full CT.gov ingestion pipeline with LLM classification.

---

## AI Chat Layer

The platform includes an AI-powered chat for exploring epigenetic oncology data.

### Endpoints
*   `POST /ai/chat` - General Q&A about drugs, targets, scores
*   `POST /ai/explain-scorecard` - Explain drug-indication scorecards
*   `POST /ai/explain-editing-asset` - Explain epigenetic editing programs
*   `GET /ai/entities` - List all known entities for autocomplete
*   `GET /ai/health` - Check AI service status

### Key Files
*   `backend/ai/client.py` - Model-agnostic AI client (Gemini)
*   `backend/ai/context_builder.py` - Build JSON context from DB
*   `backend/ai/prompts.py` - System prompts for grounding
*   `backend/api/ai_endpoints.py` - FastAPI routes

### Environment Variable
```bash
GEMINI_API_KEY=your-api-key-here  # Required for AI features
```

### Example Questions
- "What is Vorinostat used for?"
- "Why does Tazemetostat score 72 in follicular lymphoma?"
- "Compare HDAC inhibitors to BET inhibitors"
- "List all Phase 3 epigenetic drugs"

See `/docs/AI_CHAT.md` for full documentation.

---

## Key Commands

### Run the Application
```bash
# Start Backend (FastAPI)
cd /Users/mananshah/Dev/pilldreams
source venv/bin/activate
python3 -m uvicorn backend.main:app --reload --port 8000

# Start Frontend (Next.js) - in separate terminal
cd /Users/mananshah/Dev/pilldreams/frontend && npm run dev
```

### Run ETL Pipeline (Epigenetics Core Data)

**IMPORTANT**: The ETL uses CURATED seed files, NOT automated Open Targets queries.
This prevents polluting the database with irrelevant drugs (e.g., metformin showing up as an "HDAC drug").

```bash
cd /Users/mananshah/Dev/pilldreams
source venv/bin/activate

# Step 01: Seed Epigenetic Targets (67 targets from CSV)
python -m backend.etl.01_seed_epi_targets

# Step 02: Seed Gold Drugs (12 FDA-approved epigenetic drugs from CSV)
python -m backend.etl.02_build_epi_gold_drugs

# Step 03: DELETED - was pulling polluted Phase 1-3 data

# Step 04: Compute ChEMBL Metrics (potency, selectivity)
python -m backend.etl.04_compute_chembl_metrics

# Step 05: Compute BioScore & TractabilityScore (Open Targets associations)
python -m backend.etl.05_compute_bio_tract_scores

# Step 06: Compute TotalScore (50% Bio + 30% Chem + 20% Tract)
python -m backend.etl.06_compute_chem_and_total_score

# Step 07: Seed DREAM Complex Signature
python -m backend.etl.07_seed_signatures
```

### Additional ETL Scripts (Recent Additions)

```bash
# Step 20: Seed Flagship Drugs (19 high-profile drugs: PRMT5, EZH2, DOT1L, LSD1, Menin, BET inhibitors)
python -m backend.etl.20_seed_flagship_drugs

# Step 21: Expand Drugs for All Targets (via Open Targets API)
python -m backend.etl.21_expand_drugs_all_targets

# Step 22: Seed Combination Therapies (epi+IO, epi+KRAS, epi+radiation)
# NOTE: Requires epi_combos table to exist first - run SQL in Supabase Dashboard
python -m backend.etl.22_seed_epi_combos

# Step 23: Seed Target-Level Annotations (IO exhaustion, resistance roles)
# NOTE: Requires migration_target_annotations.sql to be run first
python -m backend.etl.23_seed_target_annotations
```

### SQL Migrations (run in Supabase Dashboard)
```bash
# Create epi_combos table
cat core/schema_combos.sql | pbcopy

# Add target annotations columns
cat core/migration_target_annotations.sql | pbcopy

# Then paste in Supabase Dashboard > SQL Editor > New Query > Run
```

### Curated Seed Files
- `backend/etl/seed_epi_targets.csv` - 79 epigenetic targets (DNMTs, HDACs, HMTs, KDMs, BETs, TETs, SIRTs, PRMTs, etc.)
- `backend/etl/seed_gold_drugs.csv` - 14 FDA-approved epigenetic oncology drugs
- `backend/etl/seed_flagship_drugs.csv` - 18 high-profile clinical-stage drugs (PRMT5, EZH2, DOT1L, LSD1, Menin, BET inhibitors)
- `backend/etl/seed_epi_combos.csv` - 25 combination therapy strategies (epi+IO, epi+KRAS, epi+radiation, epi+Venetoclax)
- `backend/etl/seed_target_annotations.csv` - 32 target-level annotations (IO exhaustion, resistance roles, aging clock relevance)

---

## ETL Pipeline Architecture

### Core Pipeline Order
Run these scripts in sequence to build the epigenetics database:

```
01_seed_epi_targets.py      → Load 79 targets from seed_epi_targets.csv
02_build_epi_gold_drugs.py  → Load gold drugs from seed_gold_drugs.csv
04_compute_chembl_metrics.py → ChEMBL API → potency, selectivity, richness
04c_compute_drug_phases.py   → ChEMBL API → max_phase (clinical trial phase 0-4)
05_compute_bio_tract_scores.py → Open Targets API → bio_score, tractability_score
06_compute_chem_and_total_score.py → Compute chem_score, total_score
07_seed_signatures.py        → Load DREAM complex signature
```

### Data Source Summary

| Source | Data Retrieved | Used For |
|--------|---------------|----------|
| **ChEMBL** | pXC50 (potency), delta-p (selectivity), # experiments, max_phase | ChemScore, clinical phase |
| **Open Targets** | Disease-target associations, tractability buckets | BioScore, TractabilityScore |
| **Curated CSVs** | Target definitions, gold drugs, flagship drugs | Initial seeding |

### Score Computation Flow
1. **ChEMBL** (04_) → `chembl_metrics` table → raw potency/selectivity
2. **Open Targets** (05_) → `epi_scores` table → bio_score, tractability_score
3. **Aggregation** (06_) → `epi_scores` table → chem_score, total_score

### Archived ETL Files
Files moved to `backend/etl/_archive/` (duplicates of active scripts):
- `15_seed_editing_assets.py` → duplicate of `10_seed_editing_assets.py`
- `16_compute_editing_scores.py` → duplicate of `12_compute_editing_scores.py`

---

## Database Schema (Key Tables)

### Epigenetics Core Tables
*   `epi_targets`: 79 epigenetic targets (symbol, family, class, Ensembl ID, UniProt ID, io_exhaustion_axis, epi_resistance_role, io_combo_priority, aging_clock_relevance)
*   `epi_drugs`: 66 drugs (name, ChEMBL ID, FDA approval date, source)
*   `epi_drug_targets`: Drug-target links with mechanism of action
*   `epi_indications`: 35+ oncology indications with EFO IDs
*   `epi_drug_indications`: Drug-indication links with approval status
*   `epi_scores`: BioScore, ChemScore, TractabilityScore, TotalScore per drug-indication
*   `epi_combos`: Combination therapy strategies (epi+IO, epi+KRAS, epi+radiation, etc.)
*   `epi_signatures`: Gene signatures (e.g., DREAM complex)
*   `epi_signature_targets`: Signature-target links
*   `chembl_metrics`: Chemistry data (potency, selectivity, richness)

### Current Data (as of 2025-11-30)
| Table | Count | Notes |
|-------|-------|-------|
| `epi_targets` | 79 | 20 with IO exhaustion annotations |
| `epi_drugs` | 66 | 14 FDA-approved, 18 flagship, 34 from Open Targets |
| `epi_indications` | 35 | Oncology indications with EFO/MONDO IDs |
| `epi_drug_indications` | 73 | Drug-indication pairs |
| `epi_scores` | 73 | Range: 18-70, Avg: 44 |
| `epi_combos` | 25 | 16 epi+IO, 4 radiation, 2 KRAS, 2 Venetoclax, 1 chemo |
| `epi_signatures` | 1 | DREAM complex (11 targets) |
| `chembl_metrics` | 181 | Potency/selectivity data |
| `epi_drug_targets` | 148 | Drug-target links |

### Score Distribution
- **High (≥60):** 17 drugs - VORASIDENIB (69.5), GSK126 (68.0), ENTINOSTAT (67.4)
- **Medium (40-60):** 26 drugs
- **Low (<40):** 30 drugs (early-stage or limited data)

### Combination Therapy Categories (epi_combos)
*   **epi+IO**: Epigenetic + checkpoint inhibitor (PD-1, PD-L1, CTLA-4)
*   **epi+KRAS**: Epigenetic + KRAS inhibitor (G12C, G12D)
*   **epi+radiation**: Epigenetic + radiotherapy (radiosensitization)
*   **epi+Venetoclax**: Epigenetic + BCL2 inhibitor (AML standard of care)
*   **epi+chemotherapy**: Epigenetic + cytotoxic chemotherapy

### Target-Level Annotations (20 targets annotated)
*   **io_exhaustion_axis**: Boolean - target relevant to T-cell exhaustion/IO resistance
*   **epi_resistance_role**: primary_driver | secondary | modulator
*   **io_combo_priority**: 0-100 score for IO combination prioritization
*   **aging_clock_relevance**: horvath_clock | longevity | aging_reversal

Top IO Priority Targets: EZH2 (95), BRD4 (90), HDAC1 (90), TET2 (85), PRMT5 (85)

### Legacy Tables (from old schema, may be unused)
*   `companies`: Company metadata (Ticker, Market Cap).
*   `company_assets`: Link table (Company -> Asset).
*   `user_watchlist`: User's followed companies.

### ClinicalTrials.gov Tables (NEW)
*   `ct_trials_raw`: Raw trial data from CT.gov API (audit trail).
*   `ct_trial_interventions_raw`: Expanded interventions (one row per trial-intervention).
*   `ct_trial_interventions_clean`: LLM-classified interventions (investigational/control/background).
*   `ct_trial_assets`: Trial-level asset assignments (primary sponsor ownership).
*   `pipeline_assets_ctgov`: Aggregated company-level pipeline assets.
*   `company_pipeline_qc`: QC metrics per company (coverage quality).
*   `ctgov_review_queue`: Manual review queue for ambiguous cases.
*   `llm_audit_log`: LLM usage tracking for cost/debugging.

---

## ClinicalTrials.gov Pipeline

### Overview
The CT.gov pipeline fetches clinical trial data and transforms it into clean, company-level pipeline assets.

### Pipeline Steps
1. **Fetch Trials**: Query CT.gov API v2 by sponsor name
2. **Expand Interventions**: One row per trial-intervention pair
3. **LLM Classification**: Claude classifies investigational vs. control/background drugs
4. **Assign Ownership**: Determine primary company for each asset
5. **Aggregate**: Collapse trial-level data into company-level assets
6. **Map to Internal IDs**: Link to Open Targets/ChEMBL entities
7. **QC Metrics**: Track coverage quality per company

### Key Files
*   `backend/etl/clinicaltrials.py`: CT.gov API v2 client
*   `backend/etl/ctgov_pipeline.py`: Full pipeline orchestrator
*   `scripts/run_ctgov_pipeline.py`: CLI runner script
*   `core/schema_ctgov.sql`: Database schema for CT.gov tables

---

## UI Implementation Plan

### Target User Personas & Pricing

| Persona | Price Point | Key Value Drivers |
|---------|-------------|-------------------|
| **Retail Investor** | $29-49/month | Watchlist, catalyst calendar, score transparency |
| **BD/Licensing Exec** | $25K/year (5 seats) | Deal memo generator, PowerPoint exports, competitive matrix |
| **CI Professional** | $30-50K/year | Target landscape maps, alerts, API access |
| **Drug Dev Scientist** | $5-15K/year | Biology deep dives, SAR explorer, failure analysis |

### Design System (Aceternity-Inspired)

**Color Palette** (NO red/yellow/green - use steel blue gradients):
```css
/* Backgrounds */
--bg-primary: #000000;           /* Pure black */
--bg-secondary: #0a0a0a;         /* Near black */
--bg-card: #111111;              /* Card backgrounds */
--bg-hover: #1a1a1a;             /* Hover states */

/* Borders & Lines */
--border-default: #222222;
--border-subtle: #1a1a1a;
--border-glow: rgba(255,255,255,0.1);

/* Text */
--text-primary: #ffffff;
--text-secondary: #a1a1aa;       /* zinc-400 */
--text-muted: #71717a;           /* zinc-500 */
--text-subtle: #52525b;          /* zinc-600 */

/* Accent (Steel Blue) */
--accent-primary: #60a5fa;       /* blue-400 */
--accent-secondary: #3b82f6;     /* blue-500 */
--accent-muted: #1d4ed8;         /* blue-700 */

/* Score Gradients (Steel/Silver instead of traffic lights) */
--score-high: linear-gradient(135deg, #e2e8f0, #94a3b8);      /* Silver */
--score-medium: linear-gradient(135deg, #94a3b8, #64748b);    /* Steel */
--score-low: linear-gradient(135deg, #64748b, #475569);       /* Dark Steel */

/* Glowing Effects (from Aceternity) */
--glow-gradient: radial-gradient(61.17% 178.53% at 38.83% -13.54%,
                                  #3B3B3B 0%, #888787 12.61%,
                                  #FFFFFF 50%, #888787 80%, #3B3B3B 100%);
```

**Typography**:
```css
--font-sans: 'Inter', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;

/* Sizes */
--text-h1: 3rem;      /* 48px - Page titles */
--text-h2: 1.5rem;    /* 24px - Section headers */
--text-h3: 1.125rem;  /* 18px - Card titles */
--text-body: 0.875rem; /* 14px - Data tables */
--text-caption: 0.75rem; /* 12px - Metadata */
```

### Phase 1: MVP Pages (4-6 Weeks)

#### Site Architecture
```
/                           → Landing (marketing)
/dashboard                  → Personalized Watchlist 🔐
/explore/targets            → Target Landscape (bubble chart + table)
/target/[id]                → Target Deep Dive
/company/[slug]             → Company Pipeline + TradingView
/asset/[id]                 → Asset Detail + Score Breakdown
/search                     → Global Search
```

#### Page 1: Dashboard (`/dashboard`) 🔐

**Purpose**: Personalized home for tracked entities

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│ My Watchlist                    [Add Entity] [Settings] │
├─────────────────────────────────────────────────────────┤
│ [Companies (12)] [Targets (5)] [Assets (8)]             │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ VERTEX (VRTX)│  │ LILLY (LLY)  │  │ ABBVIE (ABBV)│   │
│  │ $427.32 +2.1%│  │ $589.14 -0.8%│  │ $172.45 +1.2%│   │
│  │ 3 Pipeline   │  │ 7 Pipeline   │  │ 12 Pipeline  │   │
│  │ Next: 2025Q1 │  │ Next: 2024Q4 │  │ Next: 2025Q2 │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                          │
│  Recent Alerts (3)                        [View All]     │
└─────────────────────────────────────────────────────────┘
```

**Components Needed**: `WatchlistCard`, `TabNavigation`, `AlertFeed`, `EmptyState`

**API Endpoints**:
- `GET /api/watchlist` - User's followed entities
- `GET /api/companies/{ticker}/stock` - Real-time stock price
- `GET /api/alerts?user_id=X` - Recent alerts

#### Page 2: Target Landscape (`/explore/targets`)

**Purpose**: Visual map of all 67 epigenetic targets

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│ Target Landscape (67 Targets)         [Export] [Filter] │
├─────────────────────────────────────────────────────────┤
│ [All] [HDAC] [BET] [DNMT] [EZH2] [IDH] [Other]         │
├─────────────────────────────────────────────────────────┤
│  Bubble Chart (X: # Assets, Y: Avg BioScore)            │
│  ┌──────────────────────────────────────────────────┐   │
│  │         ○ HDAC1 (18)                             │   │
│  │   ○ BET (12)     ○ EZH2 (9)                      │   │
│  │      ○ DOT1L (4)                                 │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  Table View (sortable)                                   │
│  ┌─────────┬────────┬────────┬────────┬──────────────┐  │
│  │ Target  │ Class  │ Assets │ BioS   │ Tractability │  │
│  └─────────┴────────┴────────┴────────┴──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Components Needed**: `BubbleChart`, `TargetTable`, `FilterPanel`, `ClassPills`

**API Endpoints**:
- `GET /api/targets` - All targets with stats
- `GET /api/targets?class=HDAC` - Filter by class

#### Page 3: Target Deep Dive (`/target/[id]`)

**Purpose**: Biology, chemistry, and competitive landscape for a single target

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│ HDAC1 (Histone Deacetylase 1)          [Follow] [Export]│
├─────────────────────────────────────────────────────────┤
│ [Biology] [Chemistry] [Clinical] [Competition]          │
├─────────────────────────────────────────────────────────┤
│ Biology Tab:                                             │
│  • Target Class: Histone Deacetylase (Epigenetic Eraser)│
│  • Tractability: High (Bucket 1)                        │
│  • Disease Associations Table (BioScore by indication)  │
│                                                          │
│ Chemistry Tab:                                           │
│  • Best Potency: 2.1 nM (pXC50 = 8.7)                   │
│  • Selectivity: 3.2 log units vs HDAC2                  │
│                                                          │
│ Competition Tab:                                         │
│  • 18 Pipeline Assets Across 9 Companies                │
│    [Asset Table with TotalScore, Phase, Company]        │
└─────────────────────────────────────────────────────────┘
```

**Components Needed**: `TargetHeader`, `TabNavigation`, `BiologyPanel`, `ChemistryPanel`, `CompetitionTable`

**API Endpoints**:
- `GET /api/targets/{id}` - Target metadata
- `GET /api/targets/{id}/diseases` - Disease associations
- `GET /api/targets/{id}/chemistry` - ChEMBL stats
- `GET /api/targets/{id}/assets` - Pipeline assets

#### Page 4: Company Pipeline (`/company/[slug]`)

**Purpose**: Portfolio view with TradingView chart + scored pipeline

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│ Vertex Pharmaceuticals (VRTX)          [Follow] [Export]│
├─────────────────────────────────────────────────────────┤
│ $427.32 +2.1%                           Market Cap: $110B│
├─────────────────────────────────────────────────────────┤
│ [Chart] [Pipeline] [Trials] [News]                      │
├─────────────────────────────────────────────────────────┤
│ Chart Tab: [TradingView Embedded Widget - 1Y]           │
│                                                          │
│ Pipeline Tab:                                            │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Asset    │Target│Phase│TotalScore│Bio│Chem│Tract  │ │
│  ├──────────┼──────┼─────┼──────────┼───┼────┼───────┤ │
│  │ VX-548   │Nav1.8│ 3   │ 87       │92 │84  │85     │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Components Needed**: `CompanyHeader`, `TradingViewWidget`, `PipelineTable`, `PhaseFilter`

**API Endpoints**:
- `GET /api/companies/{slug}` - Company metadata
- `GET /api/companies/{slug}/stock` - Stock price (yfinance)
- `GET /api/companies/{slug}/assets` - Pipeline with scores

#### Page 5: Asset Detail (`/asset/[id]`)

**Purpose**: Deep dive with score breakdown

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│ VORINOSTAT (Vertex - HDAC Inhibitor)   [Follow] [Export]│
├─────────────────────────────────────────────────────────┤
│ Total Score: 68/100          [See Calculation]          │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │  ████████████████████░░░░░░░░  68                   │ │
│ │  ├─ BioScore: 82 ━━━━━━━━━━━━━━━━━━━ (50% weight)   │ │
│ │  ├─ ChemScore: 58 ━━━━━━━━━━━━━ (30% weight)        │ │
│ │  └─ TractScore: 65 ━━━━━━━━━━━━━━ (20% weight)      │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ [Overview] [Chemistry] [Trials] [Competition]           │
├─────────────────────────────────────────────────────────┤
│ Overview Tab:                                            │
│  • Target: HDAC1 (Histone Deacetylase 1)                │
│  • Indication: Multiple Myeloma                          │
│  • Phase: 4 (Approved)                                  │
│  • Company: Merck                                       │
└─────────────────────────────────────────────────────────┘
```

**Components Needed**: `AssetHeader`, `ScoreGauge`, `ScoreBreakdown`, `TabNavigation`, `TrialList`

**API Endpoints**:
- `GET /api/assets/{id}` - Asset with scores
- `GET /api/assets/{id}/chemistry` - ChEMBL data
- `GET /api/assets/{id}/trials` - CT.gov trials
- `GET /api/assets/{id}/competitors` - Same target/indication assets

#### Page 6: Global Search (`/search`)

**Purpose**: Full-text search across all entities

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│ [Search: "HDAC inhibitor multiple myeloma"]    [Advanced]│
├─────────────────────────────────────────────────────────┤
│ Results (12)                                             │
│  ┌──────────────────────────────────────────────────┐   │
│  │ [ASSET] Vorinostat (Merck - HDAC Inhibitor)      │   │
│  │ TotalScore: 68 | Phase 4 (Approved)              │   │
│  ├──────────────────────────────────────────────────┤   │
│  │ [TARGET] HDAC1 (18 Assets, BioScore 82)          │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Components Needed**: `SearchBar`, `ResultCard`, `AdvancedFilterPanel`

**API Endpoints**:
- `GET /api/search?q=hdac` - Full-text search

---

### Core Components Library

#### 1. `ScoreGauge` - Visual score display

```tsx
// Score displayed as horizontal bar with gradient fill
// Steel gradient (light to dark based on score)
<ScoreGauge
  score={68}
  max={100}
  breakdown={[
    { label: 'Bio', value: 82, weight: 50 },
    { label: 'Chem', value: 58, weight: 30 },
    { label: 'Tract', value: 65, weight: 20 }
  ]}
  showBreakdown={true}
/>
```

**Visual Style**:
- Horizontal bar with steel gradient fill (not circular)
- Score number in bold white
- Sub-scores as smaller bars below with labels
- Click to expand calculation modal

#### 2. `DataTable` - Sortable, exportable table

```tsx
<DataTable
  columns={[
    { key: 'name', label: 'Asset', sortable: true },
    { key: 'target', label: 'Target' },
    { key: 'phase', label: 'Phase', sortable: true },
    { key: 'score', label: 'Score', sortable: true, render: ScoreBadge }
  ]}
  data={assets}
  exportable={true}
  selectable={true}
/>
```

**Features**:
- Sticky header on scroll
- Sort by any column (click header)
- Row selection for comparison
- Export to Excel/CSV

#### 3. `BubbleChart` - Interactive scatter plot

```tsx
<BubbleChart
  data={targets}
  xAxis={{ key: 'asset_count', label: 'Number of Assets' }}
  yAxis={{ key: 'avg_bio_score', label: 'Avg BioScore' }}
  bubbleSize={{ key: 'experiments', label: 'Data Richness' }}
  onClick={(target) => router.push(`/target/${target.id}`)}
/>
```

**Implementation**: Recharts ScatterChart with custom tooltip

#### 4. `TradingViewWidget` - Embedded stock chart

```tsx
<TradingViewWidget
  ticker="VRTX"
  theme="dark"
  height={400}
/>
```

**Implementation**: TradingView Lightweight Charts or embed widget

#### 5. `FilterPanel` - Slide-out filter controls

```tsx
<FilterPanel
  isOpen={showFilters}
  onClose={() => setShowFilters(false)}
  filters={[
    { type: 'checkbox', key: 'class', label: 'Target Class', options: ['HDAC', 'BET', 'DNMT'] },
    { type: 'range', key: 'bioScore', label: 'BioScore', min: 0, max: 100 }
  ]}
  onApply={handleFilterApply}
/>
```

#### 6. `FollowButton` - Toggle follow/unfollow

```tsx
<FollowButton
  entityType="company"
  entityId="VRTX"
  onToggle={(followed) => toast(`${followed ? 'Following' : 'Unfollowed'} Vertex`)}
/>
```

#### 7. `ExportDropdown` - Export data in multiple formats

```tsx
<ExportDropdown
  formats={['excel', 'csv', 'pdf']}
  data={pipelineAssets}
  filename="vertex_pipeline"
/>
```

#### 8. `ScoreBadge` - Inline score indicator

```tsx
// Steel-gradient badge showing score
<ScoreBadge score={78} size="sm" />  // 78
<ScoreBadge score={45} size="md" />  // 45 (darker gradient for lower scores)
```

---

### API Layer (FastAPI Endpoints)

#### Targets API
```python
# backend/api/targets.py

@router.get("/targets")
async def list_targets(
    target_class: Optional[str] = None,
    min_bio_score: Optional[float] = None
) -> List[TargetSummary]:
    """List all targets with aggregated stats"""

@router.get("/targets/{target_id}")
async def get_target(target_id: str) -> TargetDetail:
    """Get target with biology, chemistry, and competition data"""

@router.get("/targets/{target_id}/diseases")
async def get_target_diseases(target_id: str) -> List[DiseaseAssociation]:
    """Get disease associations with BioScores"""

@router.get("/targets/{target_id}/assets")
async def get_target_assets(target_id: str) -> List[AssetSummary]:
    """Get all pipeline assets targeting this protein"""
```

#### Companies API
```python
# backend/api/companies.py

@router.get("/companies/{slug}")
async def get_company(slug: str) -> CompanyDetail:
    """Get company metadata + stock price"""

@router.get("/companies/{slug}/assets")
async def get_company_assets(slug: str) -> List[AssetWithScore]:
    """Get all pipeline assets for this company"""

@router.get("/companies/{slug}/stock")
async def get_stock_price(slug: str) -> StockQuote:
    """Get real-time stock price via yfinance"""
```

#### Assets API
```python
# backend/api/assets.py

@router.get("/assets/{asset_id}")
async def get_asset(asset_id: str) -> AssetDetail:
    """Get asset with full score breakdown"""

@router.get("/assets/{asset_id}/chemistry")
async def get_asset_chemistry(asset_id: str) -> ChemistryMetrics:
    """Get ChEMBL potency, selectivity data"""

@router.get("/assets/{asset_id}/trials")
async def get_asset_trials(asset_id: str) -> List[ClinicalTrial]:
    """Get CT.gov trials for this asset"""

@router.get("/assets/{asset_id}/competitors")
async def get_asset_competitors(asset_id: str) -> List[AssetSummary]:
    """Get competing assets (same target/indication)"""
```

#### Search API
```python
# backend/api/search.py

@router.get("/search")
async def search(
    q: str,
    entity_type: Optional[str] = None,  # 'target', 'asset', 'company'
    min_score: Optional[float] = None
) -> List[SearchResult]:
    """Full-text search across all entities"""
```

#### Watchlist API
```python
# backend/api/watchlist.py

@router.get("/watchlist")
async def get_watchlist(user_id: str) -> List[WatchlistEntity]:
    """Get user's followed entities"""

@router.post("/watchlist")
async def add_to_watchlist(
    entity_type: str,
    entity_id: str,
    user_id: str
) -> WatchlistEntity:
    """Add entity to watchlist"""

@router.delete("/watchlist/{entity_id}")
async def remove_from_watchlist(entity_id: str, user_id: str):
    """Remove entity from watchlist"""
```

---

### Implementation Order

**Week 1**: Foundation
- [ ] Update Tailwind config with design system colors
- [ ] Build `ScoreGauge`, `ScoreBadge` components
- [ ] Build `DataTable` with sorting
- [ ] Create API client (`lib/api.ts`)

**Week 2**: Core Pages
- [ ] Build `/explore/targets` with table view
- [ ] Build `/target/[id]` with tabs
- [ ] Implement FastAPI endpoints for targets

**Week 3**: Company & Asset Pages
- [ ] Build `/company/[slug]` with TradingView
- [ ] Build `/asset/[id]` with score breakdown
- [ ] Implement FastAPI endpoints for companies/assets

**Week 4**: Search & Dashboard
- [ ] Build `/search` with results
- [ ] Build `/dashboard` watchlist
- [ ] Implement watchlist API

**Week 5-6**: Polish
- [ ] Add loading skeletons
- [ ] Add error states
- [ ] Mobile responsiveness
- [ ] Excel export functionality
- any time there is a chnage to our database schema pla update the database_schema.md file in /docs/
- DO NOT delete any drugs or information without explicit approval by the user. PCSK9 drugs for example are being studied as epigenetic modifiers.
- any time the database schema is updated you need to document it in /Users/mananshah/Dev/pilldreams/docs/DATABASE_SCHEMA.md