# Project Planning & Status
**Timestamp**: 2025-11-27 3:30 PM EST

## 1. Current Status Snapshot
We have successfully pivoted the platform into a **Epigenetics Oncology Intelligence System** with a modern **Next.js Web Application**.

### The Database
*   **Targets**: Comprehensive list of epigenetic targets (Writers, Readers, Erasers).
*   **Drugs**: Approved and experimental drugs targeting these proteins.
*   **Signatures**: Epigenetic signatures and complexes.
*   **ClinicalTrials.gov Data**: Automated pipeline ingestion with LLM classification.

### The Intelligence Engine
We have implemented a **Weighted Scoring Model** based on three layers of evidence:
1.  **Biological Rationale (50%)**: Validated by Open Targets genetics & somatic mutations.
2.  **Chemistry Quality (30%)**: Validated by ChEMBL potency ($pXC_{50}$) and selectivity ($\Delta p$).
3.  **Target Tractability (20%)**: Validated by UniProt/Open Targets druggable bucket assessments.

### The Product
*   **Web Application**: A premium Next.js application (Aceternity UI) for searching and analyzing targets, drugs, and indications.
*   **Pipeline Explorer**: Ranks experimental assets by their **TotalScore**.

---

## 2. Expansion Strategy: Roadmap to Scale
To expand this foundation into a commercial-grade platform, we propose the following roadmap:

### Phase 1: Horizontal Expansion (The "Width")
*   **Objective**: Increase asset coverage by 10-20x.
*   **Action**: Expand the disease scope from 5 to the **top 50 chronic diseases** (e.g., Alzheimer's, COPD, Rheumatoid Arthritis, NASH).
*   **Implementation**: Update `config.py` with a broader list of EFO IDs.

### Phase 2: Vertical Expansion (The "Depth")
*   **Objective**: Capture novel targets and modern modalities.
*   **Action 1 (Targets)**: Ingest the full Open Targets association dataset (millions of rows) instead of just the top 1,000 per disease. This captures "hidden gems" with weaker but emerging signals.
*   **Action 2 (Modalities)**: Remove the "Small Molecule" filter to include **Antibodies**, **RNA therapies**, and **Gene Therapies**, which represent ~40% of the modern biotech pipeline.

### Phase 3: New Intelligence Layers ✅ IN PROGRESS

#### ClinicalTrials.gov Integration (COMPLETED)
*   **Source**: ClinicalTrials.gov API v2
*   **Pipeline**: `backend/etl/ctgov_pipeline.py`
*   **Features**:
    *   Fetches trials by company/sponsor name
    *   Expands multi-intervention trials into individual assets
    *   **LLM Classification** (Claude): Distinguishes investigational drugs vs. controls/background therapy
    *   Assigns primary sponsor ownership
    *   Aggregates into company-level pipeline assets
    *   Maps to Open Targets/ChEMBL IDs
    *   QC metrics per company
*   **Tables**: `ct_trials_raw`, `ct_trial_interventions_raw`, `ct_trial_interventions_clean`, `ct_trial_assets`, `pipeline_assets_ctgov`, `company_pipeline_qc`
*   **Run Command**:
    ```bash
    # Single company
    python scripts/run_ctgov_pipeline.py --company "Vertex Pharmaceuticals" --ticker VRTX

    # All companies (limit 10 for testing)
    python scripts/run_ctgov_pipeline.py --all --limit 10
    ```

#### Commercial Layer (Financial Viability) - TODO
*   *Source*: **SEC EDGAR** or **Crunchbase**.
*   *Value*: Filter out companies with <6 months of cash (high risk of program abandonment).

#### IP Layer (Patent Cliff) - TODO
*   *Source*: **USPTO** / **Google Patents**.
*   *Value*: Identify when Gold Set drugs go generic, opening the door for "Bio-betters."

### Phase 4: Company Intelligence & Watchlist (Completed)
*   **Objective**: Shift from a pure "Drug Explorer" to a "Company-First" investment tool.
*   **Implementation**:
    *   **Source**: Curated list of **32 Core Biotech Tickers** (e.g., LLY, VRTX, BIIB) enriched via `yfinance`.
    *   **Mapping**: Fuzzy matching of Pipeline Assets to Companies (e.g., "LLY-123" -> Eli Lilly).
    *   **Privacy**: Implemented a **Watchlist Mode** where global explorers are hidden, and users explicitly "Follow" companies to see their scored assets.
    *   **UI**: "AI Studio" aesthetic with Sidebar navigation and TradingView integration.
