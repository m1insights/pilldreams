# pilldreams Project Context

> **Project Directory**: `/Users/mananshah/Dev/pilldreams/`
> **Last Updated**: 2025-11-28

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
*   **ETL**: Python Scripts (`backend/etl/`)
    *   `open_targets.py`: Disease & Drug ingestion.
    *   `chembl.py`: Chemistry data.
    *   `companies.py`: Company data via `yfinance`.
    *   `clinicaltrials.py`: CT.gov API v2 client.
    *   `ctgov_pipeline.py`: Full CT.gov ingestion pipeline with LLM classification.

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

### Curated Seed Files
- `backend/etl/seed_epi_targets.csv` - 67 epigenetic targets (DNMTs, HDACs, HMTs, KDMs, BETs, TETs, SIRTs, etc.)
- `backend/etl/seed_gold_drugs.csv` - 12 FDA-approved epigenetic oncology drugs

---

## Database Schema (Key Tables)

### Epigenetics Core Tables
*   `epi_targets`: 67 epigenetic targets (symbol, family, class, Ensembl ID, UniProt ID)
*   `epi_drugs`: 12 gold drugs (name, ChEMBL ID, FDA approval date, source)
*   `epi_drug_targets`: Drug-target links with mechanism of action
*   `epi_indications`: Oncology indications with EFO IDs
*   `epi_drug_indications`: Drug-indication links with approval status
*   `epi_scores`: BioScore, ChemScore, TractabilityScore, TotalScore per drug-indication
*   `epi_signatures`: Gene signatures (e.g., DREAM complex)
*   `epi_signature_targets`: Signature-target links
*   `chembl_metrics`: Chemistry data (potency, selectivity, richness)

### Current Data (as of 2025-11-28)
| Table | Count |
|-------|-------|
| `epi_targets` | 67 |
| `epi_drugs` | 12 |
| `epi_indications` | 7 |
| `epi_scores` | 12 |
| `epi_signatures` | 1 (DREAM) |

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
