# ETL & Data Pipelines Documentation

**Last Updated:** 2025-12-02 22:30 PST

This document covers all scripts used to ingest, validate, and maintain data in the pilldreams platform.

## Overview

The platform uses a combination of:
1. **Curated seed files** (CSV) - Human-validated core data
2. **External APIs** - ChEMBL, Open Targets, ClinicalTrials.gov for automated enrichment
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
│  PATENT DISCOVERY                                                    │
│  └── 31_fetch_patents.py         → USPTO PatentsView API            │
│                                                                      │
│  CLINICAL TRIALS (ClinicalTrials.gov)                               │
│  └── 32_fetch_trial_dates.py     → Trial calendar + dates           │
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

### 17 - Ingest Patents (Manual Seeding)
```bash
python -m backend.etl.17_ingest_epi_patents
```
**Source:** `backend/etl/seed_epi_patents.csv`
**Destination:** `epi_patents` table
**Records:** 10 patents (initial seed)

Loads curated patents from CSV file. Each patent includes:
- Patent number (US, WO, EP formats)
- Title, assignee, inventor
- Publication date
- Category (epi_editor, epi_therapy, epi_diagnostic, epi_io, epi_tool)
- Related target symbols

### 31 - Fetch Patents from USPTO (Automated Discovery)
```bash
# Run all search strategies
python -m backend.etl.31_fetch_patents --strategy all

# Run specific strategy only
python -m backend.etl.31_fetch_patents --strategy technology

# Dry run (preview without database writes)
python -m backend.etl.31_fetch_patents --strategy target --dry-run --limit 20
```

**API:** USPTO PatentsView PatentSearch API (new ElasticSearch-based API)
**Environment Variable:** `PATENTSVIEW_API_KEY` (free, register at https://patentsview.org/apis/keyrequest)
**Destination:** `epi_patents` table
**Rate Limit:** 45 requests/minute

**Search Strategies:**

| Strategy | Field | Keywords |
|----------|-------|----------|
| `company` | Assignee | 30+ companies (Epizyme, Chroma, Tune, Intellia, big pharma...) |
| `target` | Abstract | 40+ target terms (HDAC, BET, EZH2, DNMT, LSD1, Menin...) |
| `technology` | Abstract | "epigenetic", "epigenetics", "epigenome", chromatin, CRISPR, dCas9... |
| `drug` | Abstract | 25+ drug names (vorinostat, tazemetostat, entinostat...) |

**Features:**
- Auto-classifies patents: `epi_editor`, `epi_therapy`, `epi_diagnostic`, `epi_io`, `epi_tool`
- Extracts related target symbols from title/abstract
- Deduplicates by patent number (upsert logic)
- Filters to last 5 years by default

**Getting an API Key:**
1. Go to https://patentsview.org/apis/keyrequest
2. Fill out the request form (free, instant)
3. Add to `.env`: `PATENTSVIEW_API_KEY=your_key_here`

**Scheduling:**
```bash
# Weekly patent discovery
0 6 * * 0 cd /path/to/pilldreams && source venv/bin/activate && python -m backend.etl.31_fetch_patents --strategy all >> logs/patent_fetch.log 2>&1
```

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

# For patent discovery
PATENTSVIEW_API_KEY=your-key         # Free: https://patentsview.org/apis/keyrequest

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

---

## Clinical Trials (ClinicalTrials.gov)

### 32 - Fetch Trial Dates
```bash
# Full run (all Tier 2 drugs)
python -m backend.etl.32_fetch_trial_dates

# Dry run (preview without database writes)
python -m backend.etl.32_fetch_trial_dates --dry-run

# Single drug only
python -m backend.etl.32_fetch_trial_dates --drug VORINOSTAT

# Tier 1 only (curated NCT IDs)
python -m backend.etl.32_fetch_trial_dates --tier1-only
```

**API:** ClinicalTrials.gov API v2 (REST)
**Destination:** `ci_trial_calendar` table
**Rate Limit:** 3 requests/second (built-in delays)

### Query Strategy (Tiered Approach)

The ETL uses a tiered query strategy to avoid polluting the database with irrelevant trials:

| Tier | Drugs | Query Method | Rationale |
|------|-------|--------------|-----------|
| **Tier 1** (Curated) | PCSK9, TTR, E2F drugs (17 total) | Fetch only specific NCT IDs from `ci_curated_trials` | These drugs have 100s of cardio/metabolic trials - only want rare epigenetic-relevant ones |
| **Tier 2** (Oncology Filter) | Core epi drugs (42 total) | Drug name + oncology conditions filter | HDAC, BET, EZH2, etc. - most trials are cancer-related |
| **Skip** | JQ1 (1 drug) | No query | Research tool only, not in clinical trials |

### Tier 1 Curated Trials

For Tier 1 drugs, you must manually add NCT IDs to `backend/etl/seed_curated_trials.csv`:

```csv
drug_name,nct_id,relevance_notes
INCLISIRAN SODIUM,NCT04659863,"ORION-18: Long-term siRNA mechanism study"
PATISIRAN SODIUM,NCT03862807,"APOLLO-B: RNAi mechanism study - gene silencing"
```

Then run:
```bash
# Load curated trials to ci_curated_trials table
# (The 32_fetch_trial_dates.py script reads from this table for Tier 1 drugs)
```

### Adding New Drugs to the Trial Calendar

**For Tier 2 drugs (default - oncology drugs):**
1. Add the drug to `epi_drugs` table (via seed CSV or Open Targets expansion)
2. Ensure `ctgov_query_tier = 'tier2_oncology'` (default)
3. Run `python -m backend.etl.32_fetch_trial_dates`

**For Tier 1 drugs (PCSK9, metabolic, non-oncology):**
1. Set `ctgov_query_tier = 'tier1_curated'` in `epi_drugs`
2. Find relevant NCT IDs manually on clinicaltrials.gov
3. Add to `backend/etl/seed_curated_trials.csv`
4. Run the ETL

**To skip a drug entirely:**
```sql
UPDATE epi_drugs SET ctgov_query_tier = 'skip' WHERE name = 'DRUG_NAME';
```

### Oncology Conditions Filter

Tier 2 queries use this OR filter to restrict to cancer trials:
```
cancer OR tumor OR carcinoma OR lymphoma OR leukemia OR myeloma OR
sarcoma OR melanoma OR neoplasm OR oncology OR malignant
```

### Data Captured

For each trial, the ETL captures:
- `nct_id` - Unique trial identifier
- `trial_title` - Brief study title
- `primary_completion_date` - When primary endpoint data available
- `primary_completion_type` - "Actual" or "Anticipated"
- `study_completion_date` - Full study completion
- `start_date` - When enrollment began
- `phase` - PHASE1, PHASE2, PHASE3, PHASE4, EARLY_PHASE1
- `status` - RECRUITING, ACTIVE_NOT_RECRUITING, COMPLETED, etc.
- `drug_id` - Link to epi_drugs
- `drug_name` - Denormalized for display
- `lead_sponsor` - Company/institution name
- `lead_sponsor_type` - INDUSTRY, NIH, OTHER
- `enrollment` - Number of participants
- `query_tier` - Which tier discovered this trial

### Scheduling

```bash
# Daily trial calendar refresh (2am EST = 7am UTC)
0 7 * * * cd /path/to/pilldreams && source venv/bin/activate && python -m backend.etl.32_fetch_trial_dates >> logs/trial_dates.log 2>&1
```

### Current Data (as of 2025-12-02)

| Metric | Value |
|--------|-------|
| Total Trials | 991 |
| Phase 3 | 63 |
| Phase 2 | 355 |
| Phase 1 | 514 |
| Currently Recruiting | 260 |
| Completed | 543 |

Top drugs: VORINOSTAT (145), DECITABINE (141), TUCIDINOSTAT (103), AZACITIDINE (102)

---

## Adding New Data to the Database

### Adding a New Drug

**Option 1: Via Curated CSV (Recommended for flagship drugs)**
1. Add to `backend/etl/seed_gold_drugs.csv` or `seed_flagship_drugs.csv`
2. Run `python -m backend.etl.02_build_epi_gold_drugs` or `20_seed_flagship_drugs`
3. Run enrichment scripts (04, 05, 06) to compute scores
4. Run `python -m backend.etl.32_fetch_trial_dates --drug DRUG_NAME` for trials

**Option 2: Via Open Targets Expansion**
1. Ensure the drug's target is in `epi_targets`
2. Run `python -m backend.etl.21_expand_drugs_all_targets`
3. Drug will be auto-discovered if it's in Open Targets

### Adding a New Target

1. Add to `backend/etl/seed_epi_targets.csv`:
   ```csv
   symbol,name,family,class,ensembl_id,uniprot_id
   NEW_TARGET,Full Target Name,TARGET_FAMILY,writer|reader|eraser,ENSG...,P12345
   ```
2. Run `python -m backend.etl.01_seed_epi_targets`
3. Run drug expansion to find drugs targeting it

### Adding a New Indication

1. Find the EFO ID on Open Targets or EBI Ontology Lookup
2. Add to `epi_indications` table directly:
   ```sql
   INSERT INTO epi_indications (efo_id, name, disease_area)
   VALUES ('EFO_0000123', 'New Cancer Type', 'Oncology');
   ```
3. Run bio/tract score computation to get associations

### Adding a New Patent (Manual)

1. Add to `backend/etl/seed_epi_patents.csv`
2. Run `python -m backend.etl.17_ingest_epi_patents`

### Adding a Curated Clinical Trial (Tier 1)

1. Add to `backend/etl/seed_curated_trials.csv`:
   ```csv
   drug_name,nct_id,relevance_notes
   DRUG_NAME,NCT12345678,"Why this trial is epigenetic-relevant"
   ```
2. Run `python -m backend.etl.32_fetch_trial_dates --tier1-only`

### Adding a Conference

Manually insert into `ci_conferences`:
```sql
INSERT INTO ci_conferences (name, short_name, start_date, end_date, abstract_deadline, year, location, oncology_focus, epigenetics_track)
VALUES ('Conference Name', 'CONF', '2026-05-01', '2026-05-05', '2026-02-01', 2026, 'City, Country', TRUE, TRUE);
```

---

## Maintenance Schedule

| Frequency | Script | Purpose |
|-----------|--------|---------|
| **Daily** | `30_fetch_news.py` | Get new articles from RSS |
| **Daily** | `32_fetch_trial_dates.py` | Refresh trial dates/status |
| **Weekly** | `04_compute_chembl_metrics.py` | Refresh chemistry data |
| **Weekly** | `05_compute_bio_tract_scores.py` | Refresh bio/tract scores |
| **Weekly** | `06_compute_chem_and_total_score.py` | Recompute total scores |
| **Weekly** | `31_fetch_patents.py` | Discover new patents |
| **Monthly** | `21_expand_drugs_all_targets.py` | Find new drugs in Open Targets |
| **Yearly** | Manual seed `ci_conferences` | Add next year's conferences |

### Cron Configuration

```bash
# Daily jobs
0 7 * * * cd /app && python -m backend.etl.32_fetch_trial_dates
0 8 * * * cd /app && python -m backend.etl.30_fetch_news

# Weekly jobs (Sunday)
0 6 * * 0 cd /app && python -m backend.etl.31_fetch_patents --strategy all
0 7 * * 0 cd /app && python -m backend.etl.04_compute_chembl_metrics
0 8 * * 0 cd /app && python -m backend.etl.05_compute_bio_tract_scores
0 9 * * 0 cd /app && python -m backend.etl.06_compute_chem_and_total_score
```
