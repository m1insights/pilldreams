# Project Planning & Status
**Timestamp**: 2025-11-27 12:23 PM EST

## 1. Current Status Snapshot
We have successfully pivoted the platform into a **Disease-Anchored Drug Intelligence System**.

### The Database
*   **Gold Standard (Approved)**: **248** drugs.
    *   *Role*: The "Control Group" / Benchmark.
    *   *Source*: Open Targets (Phase 4).
*   **Pipeline Assets (Experimental)**: **116** drugs.
    *   *Role*: The "Test Group" / Contenders.
    *   *Source*: Open Targets (Phase 1/2 Small Molecules).
*   **Diseases Covered**: 5 (MDD, GAD, ADHD, T2D, Oncology).

### The Intelligence Engine
We have implemented a **Weighted Scoring Model** based on three layers of evidence:
1.  **Biological Rationale (50%)**: Validated by Open Targets genetics & somatic mutations.
2.  **Chemistry Quality (30%)**: Validated by ChEMBL potency ($pXC_{50}$) and selectivity ($\Delta p$).
3.  **Target Tractability (20%)**: Validated by UniProt/Open Targets druggable bucket assessments.

### The Product
*   **Pipeline Explorer**: A Streamlit interface that ranks experimental assets by their **TotalScore**, allowing users to instantly spot high-potential drugs (High Bio + High Chem + High Tractability) vs. high-risk bets.

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

### Phase 3: New Intelligence Layers
*   **Clinical Layer (Real-Time Status)**:
    *   *Source*: **ClinicalTrials.gov** API.
    *   *Value*: Flag assets that are "Recruiting" vs. "Terminated" or "Withdrawn" in real-time.
*   **Commercial Layer (Financial Viability)**:
    *   *Source*: **SEC EDGAR** or **Crunchbase**.
    *   *Value*: Filter out companies with <6 months of cash (high risk of program abandonment).
*   **IP Layer (Patent Cliff)**:
    *   *Source*: **USPTO** / **Google Patents**.
    *   *Value*: Identify when Gold Set drugs go generic, opening the door for "Bio-betters."
