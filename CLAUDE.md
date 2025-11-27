# pilldreams Project Context

> **Project Directory**: `/Users/mananshah/Dev/pilldreams/`

---

## Strategic Direction (Updated 2025-11-25)

**PIVOT**: Building a **NASDAQ Biotechnology Index (NBI) Company Intelligence Platform**.

**Why**: NBI is a curated, authoritative index of biotech stocks (tracked by IBB ETF) with:
- **247 companies** - finite, manageable, and regularly updated by NASDAQ
- Direct tie to investor interests (ticker symbols, SEC filings)
- Cleaner pipeline data via company disclosures
- Clear market relevance (these are the companies investors actually trade)

**Scope**: All 247 NBI member companies loaded into database with `is_nbi_member=true` flag.

---

## Project Overview

**pilldreams** is a Streamlit web application providing **biopharma company and pipeline intelligence** for biotech investors, PharmD/MD students, clinicians, and patient advocates.

**New Flow**: Company Search → Pipeline Drugs → Approval Probability, Mechanism, Trials, Safety, Evidence, AI Chat

---

## Tech Stack

- **Frontend**: Streamlit + `streamlit-shadcn-ui`
- **Database**: Supabase (PostgreSQL)
- **Data Ingestion**: Python scripts (ClinicalTrials.gov, ChEMBL, PubMed, OpenFDA)
- **AI**: Claude (Anthropic SDK)
- **Visualization**: Plotly, RDKit (molecules)

---

## Project Structure

```
/pilldreams
├── app/
│   ├── main.py              # Streamlit entry point
│   ├── styles/custom.css    # Design system (dark theme, glass morphism)
│   └── components/          # Reusable UI components
├── core/
│   ├── scoring.py           # Scoring algorithms
│   ├── drug_name_utils.py   # Drug name normalization
│   ├── trial_design_scorer.py
│   ├── competitor_analysis.py
│   └── fda_precedent.py
├── ingestion/
│   ├── clinicaltrials.py    # Trial data
│   ├── chembl_binding.py    # Target binding affinities
│   ├── pubmed_evidence.py   # RCT/meta-analysis counts
│   ├── openfda_safety.py    # Adverse events
│   └── orange_book_patents.py
├── requirements.txt
└── CLAUDE.md
```

---

## Company Data (Primary Entity)

**Source**: NASDAQ Biotechnology Index (NBI) - scraped from investing.com/indices/nasdaq-biotechnology-components

**Scripts**:
- `ingestion/nasdaq_companies.py` - Keyword-based NASDAQ biopharma list (681 companies)
- `ingestion/update_nbi_members.py` - Mark NBI members in database
- `ingestion/add_missing_nbi.py` - Add missing NBI companies

**Current Coverage**:
- **247 NBI member companies** (is_nbi_member=true)
- ~681 total NASDAQ biopharma companies in database

**Key Companies Include**:
- Large Cap: VRTX, GILD, AMGN, REGN, BIIB, MRNA, BNTX
- Mid Cap: SAREPTA, HALOZYME, JAZZ, EXEL, NBIX
- Small Cap: Hundreds of clinical-stage biotechs

**Data Files**:
- `data/nbi_companies.csv` - 247 NBI companies with investing.com URLs
- `data/nasdaq_biopharma_companies.csv` - Full biopharma list

**Usage**:
```bash
# Update NBI member flags
python ingestion/update_nbi_members.py --update

# Add missing NBI companies
python ingestion/add_missing_nbi.py

# Verify NBI count
python ingestion/update_nbi_members.py --verify
```

---

## Database Tables (Supabase)

### NEW: Company-Centric Tables (Schema: `core/schema_company.sql`)

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `company` | Biopharma companies | ticker, name, exchange, market_category, cik, is_nbi_member, market_cap, therapeutic_focus[] |
| `company_drug` | Company-drug links | company_id, drug_id, development_stage, is_lead_program |
| `catalyst` | Stock-moving events | company_id, drug_id, catalyst_type, expected_date, confidence, is_binary_event |
| `stock_price` | Historical prices | company_id, price_date, OHLC, volume |
| `company_financials` | Quarterly financials | company_id, fiscal_quarter, revenue, cash, r_and_d_expense, runway_months |

**Note**: Run `core/schema_company.sql` in Supabase SQL Editor to create these tables.

### Existing Drug Tables (Will Link to Companies)

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `drug` | Drug master list | name, synonyms, is_approved, chembl_id |
| `target` | Molecular targets | symbol, description, uniprot_id |
| `drugtarget` | Drug-target bindings | drug_id, target_id, affinity_value, affinity_unit |
| `trial` | Clinical trials | nct_id, drug_id, phase, status, condition, enrollment |
| `safetyaggregate` | Adverse events | drug_id, meddra_term, case_count, is_serious |
| `evidenceaggregate` | Publication counts | drug_id, n_rcts, n_meta_analyses |
| `drugscore` | Computed scores | trial_score, safety_score, evidence_score, approval_probability |

---

## Data Sources & Coverage

### Company Data

| Source | Data | Coverage |
|--------|------|----------|
| NASDAQ Biotechnology Index | NBI members | **247 companies** (is_nbi_member=true) |
| Nasdaq Trader | Listed securities | 681 total biopharma companies |
| SEC EDGAR | CIK mapping | ~600 CIK identifiers for filings |

### Existing Drug Data (Will Enrich Pipelines)

| Source | Data | Current Coverage |
|--------|------|------------------|
| ClinicalTrials.gov | Trials | 26,206 drugs, 28,504 trials |
| ChEMBL | Target bindings | ~5,000+ bindings |
| PubMed | RCTs, meta-analyses | ~6,000+ drugs |
| OpenFDA | Adverse events | ~87,000+ AE records |

---

## Scoring Engine

Location: `core/scoring.py`

| Score | Range | Based On |
|-------|-------|----------|
| Trial Progress | 0-100 | Highest phase, completion rate, sponsor type, enrollment |
| Safety | 0-100 | Serious AE frequency, PRR disproportionality |
| Evidence Maturity | 0-100 | RCT count, meta-analyses, recency |
| Approval Probability | 0-1 | Weighted composite (pipeline drugs) |
| Net Benefit | 0-100 | Weighted composite (approved drugs) |

---

## Development Commands

```bash
# Run app
streamlit run app/main.py

# Run ingestion (examples)
python ingestion/chembl_binding.py
python ingestion/pubmed_evidence.py
python ingestion/openfda_safety.py

# Check background processes
ps aux | grep -E "chembl_binding|pubmed_evidence|openfda_safety" | grep -v grep
```

---

## API Rate Limits

| API | Limit |
|-----|-------|
| ClinicalTrials.gov | No strict limit (be respectful) |
| ChEMBL | Rate limited - use caching |
| PubMed | 3/sec without API key, 10/sec with key |
| OpenFDA | 240/min (40/sec) |

---

## Current Status (2025-11-24)

### Active Ingestion Jobs
Three background processes running with drug name normalization:

```bash
# Check status
tail -30 chembl_normalized_v4.log
tail -30 pubmed_normalized_v4.log
tail -30 openfda_normalized_v4.log
```

### Roadmap: Pharmacology Intelligence Platform

**Strategic Direction**: Differentiate on target science + AI synthesis. Make PhD-level pharmacology data accessible.

#### Phase 1: Complete Current Ingestion (In Progress)
- ChEMBL target bindings (~15% complete)
- PubMed RCT/meta-analysis counts (~22% complete)
- OpenFDA adverse events (~1.5% complete)

#### Phase 2: Target Science APIs (Week 1-2)

| Order | API | Table | Key Fields | Effort |
|-------|-----|-------|------------|--------|
| 1 | **Open Targets** | `target_disease` | target_id, disease_id, disease_name, association_score, genetic_evidence | 2-3 hrs |
| 2 | **DisGeNET** | `gene_disease` | gene_symbol, disease_name, score, pmid_count | 2-3 hrs |
| 3 | **KEGG** | `target_pathway` | target_id, pathway_id, pathway_name, pathway_class | 2-3 hrs |
| 4 | **STRING** | `protein_interaction` | protein_a, protein_b, combined_score, experimental_score | 2-3 hrs |

#### Phase 3: AI Chat Integration (Week 3)

| Component | Description | Effort |
|-----------|-------------|--------|
| Context Builder | Aggregate drug + targets + diseases + pathways + interactions | 3-4 hrs |
| Chat UI | Streamlit chat interface in drug detail view | 2-3 hrs |
| Prompt Engineering | System prompts for pharmacology synthesis | 2-3 hrs |
| Response Formatting | Citations, confidence indicators | 2-3 hrs |

#### Phase 4: UI for New Data (Week 4)

| Feature | Tab | Description |
|---------|-----|-------------|
| Disease Associations | Pharmacology | "This target is linked to: Depression (0.85), Anxiety (0.72)..." |
| Pathway Visualization | Pharmacology | KEGG pathway diagram or simplified view |
| Interaction Network | Pharmacology | STRING protein network (top 10 interactors) |
| AI Chat Tab | New Tab | Full conversational interface with context |

#### Data Flow Architecture

```
DRUG → TARGET (ChEMBL)
              ↓
         ┌────┴────┐
         ↓         ↓
   DISEASE    PATHWAY    INTERACTIONS
   (Open      (KEGG)     (STRING)
   Targets +
   DisGeNET)
         └────┬────┘
              ↓
         AI SYNTHESIS
         (Claude)
```

#### AI Chat Capabilities (Target)

| Question Type | Data Required | Example |
|---------------|---------------|---------|
| Mechanism Explainer | ChEMBL + KEGG | "Explain how psilocybin works at the 5-HT2A receptor" |
| Target Validation | Open Targets + DisGeNET | "Is BDNF a validated target for depression?" |
| Off-Target Risk | STRING + ChEMBL | "What other proteins might this drug affect?" |
| Competitive Biology | All above | "How does this compare to SSRIs mechanistically?" |

---

## UI Design

- **Theme**: Dark ("Bio-Financial" aesthetic)
- **Colors**: Obsidian `#050505`, Neon accents `#00FF94`/`#00C2FF`
- **Typography**: JetBrains Mono for data
- **Components**: Glass morphism cards, gradient accents
- **CSS**: `app/styles/custom.css` (design tokens, all styling)

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `app/main.py` | Main Streamlit app |
| `app/styles/custom.css` | All CSS styling |
| `core/scoring.py` | Score calculations |
| `core/drug_name_utils.py` | `normalize_drug_name()` for API queries |
| `ingestion/*.py` | Data ingestion scripts |

---

## Notes

- Drug names in DB contain dosage info (preserved for display)
- Normalization happens at query time via `drug_name_utils.normalize_drug_name()`
- App is for **informational purposes only** - not medical advice
- Respect API rate limits and terms of service

---

## Science Tab Roadmap (2025-11-25)

### Phase 1: Mechanism & Binding (Immediate)
1.  **Enrich Drugs**: Run `ingestion/chembl_binding.py` to link drugs to ChEMBL IDs and fetch binding affinities (Ki, IC50).
2.  **Fetch Targets**: Use ChEMBL IDs to identify protein targets (UniProt IDs).
3.  **Visualize**: Use `stmol` and `py3Dmol` to render 3D protein structures (PDB) in the Science tab.

### Phase 2: Validation & Context
1.  **Open Targets**: Fetch target-disease association scores.
2.  **PubMed**: Display publication counts for Drug+Disease pairs.

