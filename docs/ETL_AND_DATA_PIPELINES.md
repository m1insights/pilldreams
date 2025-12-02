# ETL & Data Pipelines Documentation

This document covers all scripts used to ingest, validate, and maintain data in the pilldreams platform.

## Overview

The platform uses a combination of:
1. **Curated seed files** (CSV) - Human-validated core data
2. **External APIs** - ChEMBL, Open Targets for automated enrichment
3. **RSS feeds** - Nature, PubMed, BioSpace for news
4. **Perplexity API** - Fact-checking and validation

```
┌─────────────────────────────────────────────────────────────────────┐
│                      DATA PIPELINE OVERVIEW                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  SEEDING (Manual/Curated)                                           │
│  ├── 01_seed_epi_targets.py      → 79 epigenetic targets            │
│  ├── 02_build_epi_gold_drugs.py  → 14 FDA-approved drugs            │
│  ├── 20_seed_flagship_drugs.py   → 18 clinical-stage drugs          │
│  ├── 22_seed_epi_combos.py       → 25 combination strategies        │
│  └── 17_ingest_epi_patents.py    → 10 patents                       │
│                                                                      │
│  ENRICHMENT (External APIs)                                         │
│  ├── 04_compute_chembl_metrics.py  → Potency, selectivity           │
│  ├── 05_compute_bio_tract_scores.py → BioScore, Tractability        │
│  ├── 06_compute_chem_and_total_score.py → Final scores              │
│  └── 21_expand_drugs_all_targets.py → Additional drugs from OT      │
│                                                                      │
│  NEWS & INTELLIGENCE                                                 │
│  └── 30_fetch_news.py            → RSS + AI analysis                │
│                                                                      │
│  VALIDATION (Perplexity)                                            │
│  └── POST /ai/fact-check/drug    → Verify drug data                 │
│  └── POST /ai/fact-check/target  → Verify target data               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Core ETL Scripts

### 01 - Seed Epigenetic Targets
```bash
python -m backend.etl.01_seed_epi_targets
```
**Source:** `backend/etl/seed_epi_targets.csv`
**Destination:** `epi_targets` table
**Records:** 79 targets

Loads curated list of epigenetic targets including:
- DNMTs, HDACs, HMTs, KDMs, BETs, TETs, SIRTs, PRMTs
- Ensembl IDs, UniProt IDs
- Target family and class classifications

### 02 - Seed Gold Drugs (FDA Approved)
```bash
python -m backend.etl.02_build_epi_gold_drugs
```
**Source:** `backend/etl/seed_gold_drugs.csv`
**Destination:** `epi_drugs`, `epi_drug_targets` tables
**Records:** 14 FDA-approved epigenetic drugs

Loads validated FDA-approved drugs:
- Vorinostat, Romidepsin, Belinostat, Panobinostat (HDAC)
- Azacitidine, Decitabine (DNMT)
- Tazemetostat (EZH2)
- Enasidenib, Ivosidenib, Olutasidenib, Vorasidenib (IDH)
- And more...

### 04 - Compute ChEMBL Metrics
```bash
python -m backend.etl.04_compute_chembl_metrics
```
**Source:** ChEMBL API
**Destination:** `chembl_metrics` table

For each drug, queries ChEMBL to get:
- **p_act_best**: Best potency (pXC50) - higher = more potent
- **p_act_median**: Median potency across assays
- **delta_p**: Selectivity (difference vs off-targets)
- **n_activities**: Number of experiments (data richness)

### 04c - Compute Drug Phases
```bash
python -m backend.etl.04c_compute_drug_phases
```
**Source:** ChEMBL API
**Destination:** `epi_drugs.max_phase` column

Updates the clinical phase (0-4) for each drug based on ChEMBL's max_phase field.

### 05 - Compute Bio & Tractability Scores
```bash
python -m backend.etl.05_compute_bio_tract_scores
```
**Source:** Open Targets API
**Destination:** `epi_scores` table

For each drug-indication pair:
- **bio_score**: Disease-target association strength (0-100)
- **tractability_score**: Druggability of target (0-100)

Uses Open Targets Platform GraphQL API.

### 06 - Compute Chem & Total Scores
```bash
python -m backend.etl.06_compute_chem_and_total_score
```
**Source:** `chembl_metrics`, `epi_scores` tables
**Destination:** `epi_scores.chem_score`, `epi_scores.total_score`

Calculates:
- **chem_score**: Normalized from ChEMBL potency/selectivity (0-100)
- **total_score**: Weighted composite: `0.5×Bio + 0.3×Chem + 0.2×Tract`

Business rules:
- If bio_score = 0 → total_score capped at 30
- If tractability_score ≤ 20 → total_score capped at 50

### 07 - Seed Signatures
```bash
python -m backend.etl.07_seed_signatures
```
**Destination:** `epi_signatures`, `epi_signature_targets` tables

Loads gene signatures like the DREAM complex (11 targets).

---

## Expansion Scripts

### 20 - Seed Flagship Drugs
```bash
python -m backend.etl.20_seed_flagship_drugs
```
**Source:** `backend/etl/seed_flagship_drugs.csv`
**Destination:** `epi_drugs`, `epi_drug_targets` tables
**Records:** 18 high-profile clinical drugs

Adds notable clinical-stage drugs:
- PRMT5 inhibitors (GSK3326595, JNJ-64619178)
- DOT1L inhibitors (Pinometostat)
- LSD1 inhibitors (Iadademstat, Bomedemstat)
- Menin inhibitors (Revumenib, Ziftomenib)
- BET inhibitors (Pelabresib, Mivebresib)

### 21 - Expand Drugs from Open Targets
```bash
python -m backend.etl.21_expand_drugs_all_targets
```
**Source:** Open Targets API
**Destination:** `epi_drugs`, `epi_drug_targets` tables

Queries Open Targets for additional drugs targeting our 79 targets.
Filters to clinical-stage compounds (phase 1+).

### 22 - Seed Combination Therapies
```bash
python -m backend.etl.22_seed_epi_combos
```
**Source:** `backend/etl/seed_epi_combos.csv`
**Destination:** `epi_combos` table
**Records:** 25 combination strategies

Categories:
- epi+IO (16): HDAC/BET + checkpoint inhibitors
- epi+radiation (4): HDAC + radiotherapy
- epi+KRAS (2): EZH2/BET + KRAS inhibitors
- epi+Venetoclax (2): EZH2/IDH + BCL-2 inhibitors
- epi+chemotherapy (1): DNMT + cytarabine

### 23 - Seed Target Annotations
```bash
python -m backend.etl.23_seed_target_annotations
```
**Source:** `backend/etl/seed_target_annotations.csv`
**Destination:** `epi_targets` columns

Adds to 20 key targets:
- `io_exhaustion_axis`: Boolean - relevant to T-cell exhaustion
- `epi_resistance_role`: primary_driver | secondary | modulator
- `io_combo_priority`: 0-100 score for IO combination
- `aging_clock_relevance`: horvath_clock | longevity | aging_reversal

---

## News & Intelligence

### 30 - Fetch News from RSS
```bash
# Full run
python -m backend.etl.30_fetch_news

# Specific source only
python -m backend.etl.30_fetch_news --source nature_drug_discovery

# Dry run (no database writes)
python -m backend.etl.30_fetch_news --dry-run

# Skip AI processing
python -m backend.etl.30_fetch_news --skip-ai

# Don't filter for epigenetics relevance
python -m backend.etl.30_fetch_news --no-filter
```

**Sources:**
| Source | Feed | Enabled |
|--------|------|---------|
| `nature_drug_discovery` | Nature Reviews Drug Discovery RSS | Yes |
| `nature_cancer` | Nature Cancer RSS | Yes |
| `biospace` | BioSpace News RSS | Yes |
| `pubmed_epigenetics` | PubMed saved search | No (needs setup) |

**Destination:** `epi_news_staging` table

**Process:**
1. Fetches RSS feeds (last 20 articles each)
2. Filters for epigenetics-relevant keywords
3. Sends to Gemini for AI analysis:
   - Generates 2-3 sentence summary
   - Extracts entities (drugs, targets, companies)
   - Classifies category (epi_drug, clinical_trial, acquisition, etc.)
   - Flags impact (bullish, bearish, neutral)
4. Inserts into staging with `status='pending'`

**Admin Workflow:**
1. Open Supabase → Table Editor → `epi_news_staging`
2. Filter: `status = 'pending'`
3. Review AI summary and extracted entities
4. Change status to `approved` or `rejected`
5. Optionally add `admin_notes` or trigger `admin_action_taken`

**Scheduling:**
Run daily via cron:
```bash
0 8 * * * cd /path/to/pilldreams && source venv/bin/activate && python -m backend.etl.30_fetch_news >> logs/news_fetch.log 2>&1
```

---

## Patent Ingestion

### 17 - Ingest Patents
```bash
python -m backend.etl.17_ingest_epi_patents
```
**Source:** `backend/etl/seed_epi_patents.csv`
**Destination:** `epi_patents` table
**Records:** 10 patents

Currently uses a curated CSV file. Each patent includes:
- Patent number (US, WO, EP formats)
- Title, assignee, inventor
- Publication date
- Category (epi_editor, epi_therapy, epi_diagnostic, epi_io, epi_tool)
- Related target symbols

### Patent Discovery (TODO)

**Current Status:** Manual curation only

**Potential Automation:**
1. **Google Patents API** - Query for epigenetic + oncology patents
2. **USPTO PatentsView API** - Search by assignee (Epizyme, Chroma, etc.)
3. **WIPO PatentScope** - International patent search

**Recommended Approach:**
```python
# Future: 31_discover_patents.py
# 1. Query by known company names (from epi_companies)
# 2. Query by target keywords (HDAC, EZH2, CRISPR epigenetic, etc.)
# 3. Filter by IPC codes: C12N15 (genetic engineering), A61K31 (drugs)
# 4. Insert new patents to epi_patents_staging for review
```

For now, manually add patents to `seed_epi_patents.csv` as you find them.

---

## Fact-Checking with Perplexity

### Overview

The fact-check system uses Perplexity's `sonar-pro` model to verify our database against current web sources. This catches:
- Acquisitions (company changed)
- Phase advances (Phase 2 → Phase 3)
- New approvals (new indications)
- Discontinued programs
- Licensing deals

### API Endpoints

#### Verify a Drug
```bash
curl -X POST http://localhost:8000/ai/fact-check/drug \
  -H "Content-Type: application/json" \
  -d '{"drug_id": "uuid-of-drug"}'
```

**Response:**
```json
{
  "entity_name": "TAZEMETOSTAT",
  "entity_type": "drug",
  "our_data": {
    "company": "Ipsen",
    "phase": 4,
    "indications": ["Follicular lymphoma", "Epithelioid sarcoma"],
    "target": "EZH2"
  },
  "verified_data": {
    "verified_company": "Ipsen (acquired from Epizyme in 2022)",
    "verified_phase": 4,
    "verified_indications": ["Follicular lymphoma", "Epithelioid sarcoma", "Endometrial cancer"],
    "recent_news": "FDA approved for endometrial cancer in 2024"
  },
  "discrepancies": [
    {
      "field": "indications",
      "ours": ["Follicular lymphoma", "Epithelioid sarcoma"],
      "verified": ["Follicular lymphoma", "Epithelioid sarcoma", "Endometrial cancer"],
      "notes": "New indication approved in 2024"
    }
  ],
  "has_discrepancies": true,
  "citations": ["https://...", "https://..."]
}
```

#### Verify a Target
```bash
curl -X POST http://localhost:8000/ai/fact-check/target \
  -H "Content-Type: application/json" \
  -d '{"target_id": "uuid-of-target"}'
```

### Fact-Check Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FACT-CHECK WORKFLOW                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  TRIGGERS                                                            │
│  ├── Manual: Admin clicks "Verify" button on drug detail page      │
│  ├── Batch: Weekly cron job for drugs not checked in 30+ days      │
│  └── Post-ETL: After importing new drugs from Open Targets         │
│                                                                      │
│  PROCESS                                                             │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │  Our Record  │───▶│  Build Prompt    │───▶│  Perplexity API  │  │
│  │  (database)  │    │  (what to verify)│    │  (sonar-pro)     │  │
│  └──────────────┘    └──────────────────┘    └──────────────────┘  │
│                                                       │              │
│                                                       ▼              │
│                                              ┌──────────────────┐   │
│                                              │  Parse Response  │   │
│                                              │  Find Diffs      │   │
│                                              └──────────────────┘   │
│                                                       │              │
│                                                       ▼              │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    ADMIN REVIEW                                 │ │
│  │  Supabase → fact_check_log table → Filter: has_discrepancies   │ │
│  │                                                                 │ │
│  │  For each discrepancy:                                         │ │
│  │  • [Confirm] - Mark as reviewed, no action needed              │ │
│  │  • [Update DB] - Update our record with verified data          │ │
│  │  • [Dispute] - Flag as incorrect/needs investigation           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Batch Fact-Check Script (TODO)

```bash
# Future: python -m backend.etl.40_batch_fact_check

# Options:
# --stale-days 30     # Check drugs not verified in 30+ days
# --limit 10          # Only check 10 drugs per run (API cost control)
# --category approved # Only check FDA-approved drugs
```

### Cost Considerations

Perplexity API pricing (as of 2024):
- sonar-pro: ~$5 per 1000 requests
- Each drug fact-check = 1 request

Recommended schedule:
- FDA-approved drugs: Weekly
- Phase 3 drugs: Bi-weekly
- Phase 1-2 drugs: Monthly
- Targets: Quarterly

---

## Running the Full Pipeline

### Initial Setup (New Database)
```bash
# 1. Seed core data
python -m backend.etl.01_seed_epi_targets
python -m backend.etl.02_build_epi_gold_drugs
python -m backend.etl.20_seed_flagship_drugs
python -m backend.etl.07_seed_signatures

# 2. Enrich with external APIs
python -m backend.etl.04_compute_chembl_metrics
python -m backend.etl.04c_compute_drug_phases
python -m backend.etl.05_compute_bio_tract_scores
python -m backend.etl.06_compute_chem_and_total_score

# 3. Add combinations and annotations
python -m backend.etl.22_seed_epi_combos
python -m backend.etl.23_seed_target_annotations

# 4. Add patents
python -m backend.etl.17_ingest_epi_patents

# 5. Start news ingestion
python -m backend.etl.30_fetch_news
```

### Ongoing Maintenance

| Frequency | Script | Purpose |
|-----------|--------|---------|
| Daily | `30_fetch_news.py` | Get new articles |
| Weekly | `04_compute_chembl_metrics.py` | Refresh chemistry data |
| Weekly | `05_compute_bio_tract_scores.py` | Refresh bio/tract scores |
| Weekly | `06_compute_chem_and_total_score.py` | Recompute total scores |
| Weekly | Fact-check approved drugs | Catch updates |
| Monthly | `21_expand_drugs_all_targets.py` | Find new drugs |
| As needed | Add patents manually | New IP filings |

---

## Environment Variables

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# For AI features
GEMINI_API_KEY=your-gemini-key       # News analysis
PERPLEXITY_API_KEY=your-pplx-key     # Fact-checking

# Optional
LOG_LEVEL=INFO
```

---

## Troubleshooting

### ChEMBL API Errors
- Rate limit: Add 1-second delay between requests
- Timeout: Increase timeout to 60 seconds
- No data: Drug may not be in ChEMBL (try alternate names)

### Open Targets API Errors
- GraphQL errors: Check query syntax
- No associations: Target may not have disease links

### News Fetcher Issues
- "Feed parsing issue": RSS feed may be malformed (BioSpace known issue)
- No articles: Keywords may be too restrictive

### Perplexity Errors
- 401: Check API key
- 429: Rate limited, wait and retry
- Parsing errors: AI response not in expected JSON format
