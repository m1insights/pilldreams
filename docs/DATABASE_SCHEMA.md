# Epigenetics Drug Intelligence Database Schema

**Last Updated:** 2025-12-03

## Overview

This database tracks epigenetic oncology drugs, their molecular targets, disease indications, and computed investment scores. It is designed to help identify promising drug development opportunities in the epigenetics space.

The schema also supports **epigenetic editing assets** (CRISPR/TALE-based gene editors) and **refresh tracking** for ongoing data maintenance.

## Core Entities

### EPI_DRUGS (60 records)
The central entity representing drug compounds. Each drug has:
- A unique ID and name (e.g., "VORINOSTAT", "TAZEMETOSTAT")
- A drug type (typically "Small molecule", "Antibody", or "Oligonucleotide")
- A ChEMBL ID for linking to public chemistry databases (e.g., "CHEMBL98")
- An Open Targets drug ID for linking to Open Targets Platform
- An FDA approval flag (true/false) indicating whether the drug is approved or still in pipeline
- **max_phase**: Maximum clinical trial phase (0=Preclinical, 1-4=Clinical phases, 4=Approved) from ChEMBL
- A first approval date (if approved)
- A source field indicating where the drug record originated ("Curated_Gold", "OpenTargets")
- **modality**: Drug modality - "small_molecule" or "biologic"
- **is_epi_io**: Flag indicating if the drug is relevant to epigenetic immuno-oncology
- **is_nsd2_targeted**: Flag indicating if the drug targets NSD2
- **last_ot_refresh**: Timestamp of last Open Targets API refresh
- **last_chembl_refresh**: Timestamp of last ChEMBL API refresh
- **ctgov_query_tier**: ClinicalTrials.gov query strategy:
  - `tier1_curated`: Only query specific NCT IDs from ci_curated_trials (for PCSK9, TTR, etc.)
  - `tier2_oncology`: Query by drug name + oncology conditions filter (default for core epi drugs)
  - `skip`: Do not query CT.gov for this drug (e.g., JQ1 research tool)
- Timestamps for creation and updates

### EPI_TARGETS (79 records)
Molecular targets (proteins) that drugs act upon. Each target has:
- A unique ID and gene symbol (e.g., "HDAC1", "BRD4", "EZH2")
- A full name describing the protein
- A family classification (e.g., "HDAC", "BET", "DNMT", "HMT", "KDM", "IDH", "SIRT")
- A class indicating the epigenetic function: "writer" (adds marks), "reader" (recognizes marks), or "eraser" (removes marks)
- An Ensembl gene ID for genomic reference
- A UniProt ID for protein reference
- An Open Targets target ID for linking to Open Targets Platform
- A flag indicating if this is a core epigenetic target
- **io_exhaustion_axis**: Boolean flag for T-cell exhaustion/IO relevance (e.g., TET2, DNMT3A)
- **epi_resistance_role**: Role in resistance mechanisms ("primary_driver", "secondary", "modulator")
- **aging_clock_relevance**: Text describing role in epigenetic aging clocks (e.g., "horvath_clock", "longevity", "aging_reversal")
- **io_combo_priority**: Integer 0-100 priority score for IO combination studies
- **annotation_notes**: Free text notes about target annotations
- **last_ot_refresh**: Timestamp of last Open Targets API refresh
- **last_chembl_refresh**: Timestamp of last ChEMBL API refresh
- Timestamps for creation and updates

### EPI_INDICATIONS (35 records)
Disease indications that drugs are developed to treat. Each indication has:
- A unique ID
- An EFO ID (Experimental Factor Ontology) for standardized disease identification (e.g., "EFO_0000222" for acute myeloid leukemia)
- A disease name (e.g., "Acute myeloid leukemia", "Multiple myeloma", "Cutaneous T-cell lymphoma")
- A disease area (all are "Oncology" in this dataset)
- **last_ot_refresh**: Timestamp of last Open Targets API refresh
- A creation timestamp

### EPI_COMPANIES (24 records)
Pharmaceutical and biotech companies developing epigenetic drugs. Each company has:
- A unique ID and company name (e.g., "Bristol-Myers Squibb", "Ipsen", "Oryzon Genomics")
- A stock ticker symbol if publicly traded (e.g., "BMY", "GILD", "IPN.PA" for European stocks) or null if private
- A stock exchange (e.g., "NYSE", "NASDAQ", "Euronext Paris", "BME (Madrid)")
- Market cap in USD
- **status**: Company status - "active" (trading), "acquired" (bought by another company), "bankrupt" (Chapter 11/7), or "delisted"
- **acquirer**: Name of acquiring company if status is "acquired" (e.g., "Novartis AG (NVS)")
- **acquisition_date**: Date of acquisition completion
- **status_notes**: Additional context about status change
- Sector and industry classifications
- A description of the company's focus
- Logo URL and website
- Headquarters location and founding year
- Employee count
- An epigenetics focus score (0-100) indicating how central epigenetics is to their business
- A pure-play flag (true if the company focuses exclusively on epigenetics)
- Timestamps for creation and updates

**Notable Status Changes (as of 2025-12-01):**
- OMGA (Omega Therapeutics): Bankrupt (Chapter 11, Feb 2025)
- SPPI (Spectrum Pharma): Acquired by Assertio (July 2023)
- MOR (MorphoSys): Acquired by Novartis for $2.9B (May 2024)
- VERV (Verve Therapeutics): Acquired by Eli Lilly for $1.3B (July 2025)

## Relationship Tables

### EPI_DRUG_TARGETS (148 records)
Links drugs to the targets they act upon. This is a many-to-many relationship (a drug can hit multiple targets, and a target can be hit by multiple drugs). Each link has:
- A unique ID
- A drug ID (foreign key to EPI_DRUGS)
- A target ID (foreign key to EPI_TARGETS)
- A mechanism of action describing how the drug affects the target (e.g., "Pan-HDAC inhibitor", "EZH2 inhibitor", "IDH1 inhibitor")
- A flag indicating if this is the primary target for the drug
- A creation timestamp

### EPI_DRUG_INDICATIONS (73 records)
Links drugs to the indications they are being developed for. This is a many-to-many relationship (a drug can target multiple diseases, and a disease can have multiple drugs in development). Each link has:
- A unique ID
- A drug ID (foreign key to EPI_DRUGS)
- An indication ID (foreign key to EPI_INDICATIONS)
- An approval status for this specific drug-indication pair
- A maximum clinical phase reached (1, 2, 3, or 4 for approved)
- A creation timestamp

## Scoring Tables

### EPI_SCORES (73 records)
Contains computed investment scores for each drug-indication pair. Each score record has:
- A unique ID
- A drug ID (foreign key to EPI_DRUGS)
- An indication ID (foreign key to EPI_INDICATIONS)
- A BioScore (0-100): Measures the biological rationale based on Open Targets disease-target association strength. Higher scores mean stronger genetic/biological evidence linking the drug's target to the disease.
- A ChemScore (0-100): Measures chemistry quality based on ChEMBL bioactivity data including potency (how strongly the drug binds), selectivity (how specific it is to the intended target vs off-targets), and data richness (how many experiments support the data).
- A TractabilityScore (0-100): Measures how "druggable" the target is based on Open Targets tractability assessments. Higher scores mean the target has structural features amenable to small molecule binding.
- A TotalScore (0-100): The weighted composite score calculated as: TotalScore = (0.5 × BioScore) + (0.3 × ChemScore) + (0.2 × TractabilityScore)
- A timestamp for when the score was last computed

### CHEMBL_METRICS (181 records)
Contains raw chemistry data fetched from ChEMBL for each drug. Each record has:
- A unique ID
- A drug ID (foreign key to EPI_DRUGS)
- p_act_median: Median pActivity value (negative log of IC50/EC50) across all assays
- p_act_best: Best (highest) pActivity value, indicating maximum potency observed
- p_off_best: Best pActivity against off-target proteins
- delta_p: Selectivity window (p_act_best minus p_off_best). Higher values indicate better selectivity.
- n_activities_primary: Number of bioactivity measurements against the primary target
- n_activities_total: Total number of bioactivity measurements in ChEMBL
- chem_score: Computed chemistry score (0-100) derived from potency, selectivity, and richness
- A creation timestamp

### CHEMBL_TARGET_ACTIVITIES
Per-target activity data for potency visualization. Each record represents activity against one target for one drug:
- A unique ID
- **drug_id**: Foreign key to EPI_DRUGS
- **target_chembl_id**: ChEMBL target ID (e.g., "CHEMBL325" for HDAC1)
- **target_name**: Human-readable target name (e.g., "Histone deacetylase 1")
- **target_type**: Target classification
- **best_pact**: Best pActivity value (pXC50) - higher = more potent
- **median_pact**: Median pActivity across all measurements
- **best_value_nm**: Best activity value in nanomolar (IC50/Ki)
- **n_activities**: Number of activity measurements
- **activity_types**: JSON array of assay types (e.g., ["IC50", "Ki"])
- **is_primary_target**: Boolean flag for primary vs off-target

Used by the frontend potency chart to visualize drug selectivity profiles across multiple targets.

## Epigenetic Editing Tables

These tables track next-generation epigenetic editing programs (CRISPR/TALE-based gene silencing).

### EPI_EDITING_ASSETS (17 records)
Epigenetic editing programs from companies like Tune Therapeutics, Chroma Medicine, etc. Each asset has:
- A unique ID and program name (e.g., "TUNE-401", "CHROMA-PCSK9")
- **sponsor**: Company developing the asset
- **modality**: Always "epigenetic_editor"
- **delivery_type**: Delivery mechanism (e.g., "LNP_mRNA", "AAV")
- **dbd_type**: DNA-binding domain type (e.g., "CRISPR_dCas9", "TALE", "ZF")
- **effector_type**: Effector strategy (e.g., "combo", "eraser", "indirect_repressor")
- **effector_domains**: JSON array of effector domains (e.g., ["DNMT3A", "DNMT3L", "KRAB"])
- **target_gene_symbol**: Target gene being silenced (e.g., "PCSK9", "MYC")
- **target_gene_id**: Foreign key to EPI_TARGETS
- **indication_id**: Foreign key to EPI_INDICATIONS
- **phase**: Clinical phase (1, 2, 3, or null for preclinical)
- **status**: Development status ("preclinical", "clinical")
- **description**: Notes about the program
- **source_url**: Reference URL

### EPI_EDITING_SCORES (17 records)
Computed scores for epigenetic editing assets. Each score record has:
- A unique ID
- **editing_asset_id**: Foreign key to EPI_EDITING_ASSETS
- **indication_id**: Foreign key to EPI_INDICATIONS
- **target_bio_score**: Biology score from Open Targets (0-100)
- **editing_modality_score**: Score based on delivery/DBD/effector combination (0-100)
- **durability_score**: Score based on durability data (NHP, mouse, in vitro) (0-100)
- **total_editing_score**: Weighted composite: (0.5 × Bio) + (0.3 × Modality) + (0.2 × Durability)

## Patent & News Tables

### EPI_PATENTS (10 records)
Epigenetics-related patents. Each patent has:
- A unique ID
- **patent_number**: USPTO/EPO/WIPO number (e.g., "US12098399B2")
- **title**: Patent title
- **assignee**: Patent owner/company
- **first_inventor**: Lead inventor name
- **pub_date**: Publication date
- **category**: Patent type ("epi_editor", "epi_therapy", "epi_io", "epi_diagnostic", "epi_tool")
- **abstract_snippet**: Brief description
- **related_target_symbols**: JSON array of related target gene symbols

### EPI_NEWS (0 records - placeholder)
News articles related to epigenetics. Structure includes:
- A unique ID
- **headline**: Article headline
- **source**: Publication source
- **pub_date**: Publication date
- **url**: Link to article
- **summary**: Brief summary
- **related_companies**: JSON array of related company names
- **related_targets**: JSON array of related target symbols
- **sentiment**: Sentiment classification ("positive", "neutral", "negative")

## Data Maintenance Tables

### ETL_REFRESH_LOG
Audit trail tracking when external APIs were queried. Each record has:
- A unique ID
- **entity_type**: Type of entity refreshed ("target", "drug", "indication")
- **entity_id**: UUID of the entity
- **api_source**: API that was queried ("open_targets", "chembl", "clinicaltrials")
- **refresh_date**: When the refresh occurred
- **records_found**: Number of records returned
- **status**: Result status ("success", "error", "no_data")
- **error_message**: Error details if applicable

## Company-Drug Relationships

Companies are linked to drugs through a view called **V_EPI_COMPANY_DRUGS** which connects companies to the drugs in their pipeline. This enables queries like "show me all drugs developed by Bristol-Myers Squibb" or "which companies are developing HDAC inhibitors."

## Key Relationships Summary

1. A DRUG targets one or more TARGETS (via EPI_DRUG_TARGETS)
2. A DRUG is developed for one or more INDICATIONS (via EPI_DRUG_INDICATIONS)
3. Each DRUG-INDICATION pair has one SCORE record with Bio/Chem/Tract/Total scores
4. Each DRUG has one CHEMBL_METRICS record with raw chemistry data
5. Each DRUG is developed by one or more COMPANIES (via company-drug links)
6. TARGETS belong to families (HDAC, BET, DNMT, etc.) and classes (writer, reader, eraser)
7. COMPANIES can be public (have ticker) or private, and pure-play or diversified

## Scoring Logic

The TotalScore prioritizes biological rationale (50% weight) because strong disease-target associations predict clinical success. Chemistry quality (30% weight) ensures the drug has good potency and selectivity. Tractability (20% weight) confirms the target is structurally suitable for drug development.

Additional business rules:
- If BioScore = 0, TotalScore is capped at 30 (weak biology is a red flag)
- If TractabilityScore ≤ 20, TotalScore is capped at 50 (undruggable targets are risky)

## Combination Therapy Table

### EPI_COMBOS (25 records)
Tracks combination therapy strategies pairing epigenetic drugs with other modalities. Each record has:
- A unique ID
- **combo_label**: Category of combination ("epi+IO", "epi+KRAS", "epi+radiation", "epi+Venetoclax", "epi+chemotherapy")
- **epi_drug_id**: Foreign key to EPI_DRUGS (the epigenetic component)
- **partner_drug_id**: Optional foreign key to EPI_DRUGS if partner is also in our database
- **partner_class**: Drug class of partner (e.g., "PD-1_inhibitor", "KRAS_G12C_inhibitor", "radiation")
- **partner_drug_name**: Name of partner drug (e.g., "PEMBROLIZUMAB", "SOTORASIB")
- **indication_id**: Foreign key to EPI_INDICATIONS
- **max_phase**: Clinical phase (0=preclinical, 1-4=clinical phases)
- **nct_id**: ClinicalTrials.gov identifier if applicable
- **source**: Data source ("OpenTargets", "PubMed", "Review", "CompanyPR", "ClinicalTrials")
- **notes**: Additional context

Combination categories:
- **epi+IO** (16 records): HDACi/BETi + checkpoint inhibitors
- **epi+radiation** (4 records): HDACi + radiotherapy
- **epi+KRAS** (2 records): EZH2i/BETi + KRAS inhibitors
- **epi+Venetoclax** (2 records): EZH2i/IDHi + BCL-2 inhibitors
- **epi+chemotherapy** (1 record): DNMTi + cytarabine

## Current Data Statistics

- 60 drugs (14 FDA-approved, 18 flagship clinical-stage, 28 from Open Targets)
  - Includes PCSK9 inhibitors (being studied as epigenetic modifiers), TTR drugs, and other targets
  - Salt form duplicates consolidated (e.g., INCLISIRAN SODIUM kept, INCLISIRAN removed)
- 79 epigenetic targets across 7+ protein families (20 with IO annotations)
- 35 oncology indications
- 148 drug-target relationships
- 73 drug-indication pairs with scores
- 73 computed scores (range: 18-70, average: 44)
- 25 combination therapy strategies
- 181 ChEMBL chemistry records
- 24 companies (16 public, 8 private)
- 17 epigenetic editing assets
- 10 patents
- **991 clinical trials in trial calendar** (as of 2025-12-02)
  - Phase 3: 63 trials
  - Phase 2: 355 trials
  - Phase 1: 514 trials
  - Currently Recruiting: 260
  - Completed: 543

### Score Distribution
- **High (≥60):** 17 drugs - Top: VORASIDENIB (69.5), GSK126 (68.0), ENTINOSTAT (67.4)
- **Medium (40-60):** 26 drugs
- **Low (<40):** 30 drugs (early-stage or limited data)

## Entity Relationship Diagram

```
┌─────────────────────┐         ┌─────────────────────┐
│     EPI_DRUGS       │         │    EPI_TARGETS      │
│─────────────────────│         │─────────────────────│
│ id (PK)             │         │ id (PK)             │
│ name                │◄───┐    │ symbol              │
│ chembl_id           │    │    │ family              │
│ fda_approved        │    │    │ class               │
│ ...                 │    │    │ ot_target_id        │
└─────────┬───────────┘    │    └──────────┬──────────┘
          │                │               │
          │    ┌───────────┴───────────┐   │
          │    │   EPI_DRUG_TARGETS    │   │
          │    │───────────────────────│   │
          │    │ drug_id (FK) ─────────┼───┘
          │    │ target_id (FK) ───────┼───►
          │    │ mechanism_of_action   │
          │    └───────────────────────┘
          │
          │    ┌───────────────────────┐
          │    │ EPI_DRUG_INDICATIONS  │
          │    │───────────────────────│
          ├───►│ drug_id (FK)          │
          │    │ indication_id (FK) ───┼───►┌─────────────────────┐
          │    │ approval_status       │    │  EPI_INDICATIONS    │
          │    └───────────┬───────────┘    │─────────────────────│
          │                │               │ id (PK)             │
          │                │               │ efo_id              │
          │    ┌───────────┴───────────┐   │ name                │
          │    │     EPI_SCORES        │   └─────────────────────┘
          │    │───────────────────────│
          ├───►│ drug_id (FK)          │
          │    │ indication_id (FK)    │
          │    │ bio_score             │
          │    │ chem_score            │
          │    │ tractability_score    │
          │    │ total_score           │
          │    └───────────────────────┘
          │
          │    ┌───────────────────────┐
          │    │   CHEMBL_METRICS      │
          │    │───────────────────────│
          └───►│ drug_id (FK)          │
               │ p_act_best            │
               │ delta_p               │
               │ chem_score            │
               └───────────────────────┘

┌─────────────────────┐
│   EPI_COMPANIES     │
│─────────────────────│
│ id (PK)             │
│ name                │───► Linked to drugs via V_EPI_COMPANY_DRUGS view
│ ticker              │
│ epi_focus_score     │
│ is_pure_play_epi    │
└─────────────────────┘

## Epigenetic Editing ERD

┌──────────────────────────┐       ┌─────────────────────┐
│   EPI_EDITING_ASSETS     │       │    EPI_TARGETS      │
│──────────────────────────│       │─────────────────────│
│ id (PK)                  │       │ id (PK)             │
│ name                     │       │ symbol              │
│ sponsor                  │       └──────────┬──────────┘
│ delivery_type            │                  │
│ dbd_type                 │                  │
│ effector_domains         │                  │
│ target_gene_id (FK) ─────┼──────────────────┘
│ indication_id (FK) ──────┼──────────────────┐
│ phase                    │                  │
│ status                   │                  ▼
└───────────┬──────────────┘       ┌─────────────────────┐
            │                      │  EPI_INDICATIONS    │
            │                      └─────────────────────┘
            │
            │    ┌─────────────────────────┐
            │    │  EPI_EDITING_SCORES     │
            │    │─────────────────────────│
            └───►│ editing_asset_id (FK)   │
                 │ indication_id (FK)      │
                 │ target_bio_score        │
                 │ editing_modality_score  │
                 │ durability_score        │
                 │ total_editing_score     │
                 └─────────────────────────┘

## Supporting Tables ERD

┌─────────────────────────┐       ┌─────────────────────┐
│     EPI_PATENTS         │       │   ETL_REFRESH_LOG   │
│─────────────────────────│       │─────────────────────│
│ id (PK)                 │       │ id (PK)             │
│ patent_number           │       │ entity_type         │
│ title                   │       │ entity_id           │
│ assignee                │       │ api_source          │
│ pub_date                │       │ refresh_date        │
│ category                │       │ records_found       │
│ related_target_symbols  │       │ status              │
└─────────────────────────┘       └─────────────────────┘
```

## News & Intelligence Tables

### EPI_NEWS_STAGING
Staging table for news articles fetched from RSS feeds, pending admin review in Supabase Table Editor. Each record has:
- A unique ID
- **source**: Feed source identifier ("nature_drug_discovery", "pubmed", "biospace", "company_pr")
- **source_url**: Original article URL
- **source_id**: RSS GUID or PubMed ID for deduplication
- **title**: Article title
- **abstract**: Article abstract/summary from RSS (not full article due to copyright)
- **pub_date**: Publication date
- **authors**: Array of author names
- **ai_summary**: AI-generated 2-3 sentence summary
- **ai_category**: Classification ("epi_drug", "epi_editing", "epi_io", "clinical_trial", "acquisition", "regulatory", "research", "other")
- **ai_impact_flag**: Market signal ("bullish", "bearish", "neutral", "unknown")
- **ai_extracted_entities**: JSON with extracted drugs, targets, companies
- **ai_confidence**: 0-1 confidence score
- **linked_drug_ids**: Array of UUIDs linking to EPI_DRUGS
- **linked_target_ids**: Array of UUIDs linking to EPI_TARGETS
- **status**: Workflow status ("pending", "approved", "rejected", "actioned")
- **admin_notes**: Admin comments
- **admin_action_taken**: What action was taken ("published", "updated_drug_phase", "added_indication", etc.)
- **reviewed_at**: Timestamp of review
- **reviewed_by**: Admin identifier

Admin workflow:
1. RSS fetcher runs daily → inserts articles with status='pending'
2. Admin opens Supabase Table Editor → filters status='pending'
3. Admin reviews AI summary and changes status to 'approved' or 'rejected'
4. Frontend shows only status='approved' articles

### FACT_CHECK_LOG
Audit trail for Perplexity API fact-checks on drugs/targets/companies. Each record has:
- A unique ID
- **entity_type**: Type being checked ("drug", "target", "company")
- **entity_id**: UUID of the entity
- **entity_name**: Name for display
- **our_data**: JSON snapshot of our database record at check time
- **perplexity_response**: Raw API response
- **perplexity_summary**: Parsed summary text
- **discrepancies**: JSON array of differences found (field, ours, verified, notes)
- **has_discrepancies**: Boolean flag for quick filtering
- **status**: Resolution status ("pending", "confirmed", "updated", "disputed")
- **resolution_notes**: Admin notes on resolution
- **resolved_at**: Timestamp of resolution
- **resolved_by**: Admin identifier
- **checked_at**: Timestamp of API call

Used to:
- Track data quality and freshness
- Identify outdated information (acquisitions, phase changes, new approvals)
- Maintain audit trail for regulatory compliance

## Competitive Intelligence Tables

### CI_TRIAL_CALENDAR
Clinical trial dates from ClinicalTrials.gov for the Trial Readout Calendar feature. Each record has:
- A unique ID
- **nct_id**: ClinicalTrials.gov identifier (e.g., "NCT04659863")
- **trial_title**: Brief title of the study
- **primary_completion_date**: When the trial's primary endpoint data will be available
- **primary_completion_type**: "Actual" or "Anticipated"
- **study_completion_date**: Full study completion date
- **start_date**: When the trial started enrolling
- **phase**: Clinical phase ("Phase 1", "Phase 2", "Phase 3", "Phase 4", "Early Phase 1")
- **status**: Trial status ("Recruiting", "Active, not recruiting", "Completed", "Terminated", etc.)
- **drug_id**: Foreign key to EPI_DRUGS
- **drug_name**: Denormalized for quick display
- **indication_id**: Foreign key to EPI_INDICATIONS
- **lead_sponsor**: Company/institution running the trial
- **lead_sponsor_type**: "Industry", "Academic", "NIH", "Other"
- **enrollment**: Number of participants
- **query_tier**: How this trial was discovered ("tier1_curated", "tier2_oncology", "tier3_discovery")
- **last_api_update**: When we last refreshed from CT.gov

Query Strategy:
- Tier 1 drugs (PCSK9, TTR): Only fetch curated NCT IDs to avoid cardiovascular trial pollution
- Tier 2 drugs (HDAC, BET, EZH2): Query by drug name + oncology conditions filter
- Tier 3: Mechanism-based discovery for new trials

### CI_CURATED_TRIALS
Manually curated NCT IDs for Tier 1 drugs where automated oncology filtering would return irrelevant trials:
- **drug_id**: Foreign key to EPI_DRUGS
- **drug_name**: Drug name for CSV import
- **nct_id**: The specific NCT ID to fetch
- **relevance_notes**: Why this trial is epigenetic-relevant

### CI_CONFERENCES
Major oncology conferences for the catalyst calendar. Seeded yearly:
- **name**: Full conference name (e.g., "ASCO Annual Meeting")
- **short_name**: Abbreviation (e.g., "ASCO")
- **start_date**: Conference start date
- **end_date**: Conference end date
- **abstract_deadline**: When abstracts are due
- **year**: Conference year
- **location**: City/venue
- **oncology_focus**: Boolean
- **epigenetics_track**: Boolean - has dedicated epigenetics sessions

### CI_CHANGE_LOG
Audit trail of all changes detected across entities for weekly digests and alerts:
- **entity_type**: "drug", "trial", "company", "patent", "news"
- **entity_id**: UUID of the changed entity
- **entity_name**: Name for display
- **change_type**: "phase_change", "status_change", "new_entity", "score_change", "date_change"
- **field_changed**: Which field changed
- **old_value**: Previous value
- **new_value**: New value
- **significance**: "low", "medium", "high", "critical"
- **source**: "ctgov", "fda", "news", "patent", "manual"
- **digest_sent**: Boolean - has this been included in a digest email

Significance levels:
- Critical: FDA approval, Phase 2→3 advancement, company acquisition
- High: Trial terminated, new IND filing
- Medium: Completion date change, new patent
- Low: News mention, score recalculation

### CI_USER_DIGEST_PREFS
User preferences for receiving weekly/daily change digest emails:
- **user_id**: Optional Supabase Auth user ID
- **email**: Email address for digest delivery (unique)
- **name**: Display name
- **digest_frequency**: "daily", "weekly", "monthly", "never"
- **digest_day**: Day of week for weekly digest (0=Sunday, 1=Monday, etc.)
- **digest_hour**: Hour of day (0-23) in user's timezone
- **digest_timezone**: Timezone string (default: "America/New_York")
- **min_significance**: Minimum change level to include ("low", "medium", "high", "critical")
- **entity_types**: Array of entity types to include (default: ['drug', 'trial', 'target'])
- **watched_drug_ids**: Optional array of specific drug UUIDs to track
- **watched_target_ids**: Optional array of specific target UUIDs to track
- **filter_to_watchlist**: If true, only include changes to watched entities
- **slack_webhook_url**: Optional Slack integration
- **is_active**: Boolean - is subscription active
- **email_verified**: Boolean - has email been verified
- **last_digest_sent**: Timestamp of last sent digest

### CI_DIGEST_HISTORY
Audit trail of sent digests for tracking and debugging:
- **user_id**: Foreign key to CI_USER_DIGEST_PREFS
- **email**: Email address (denormalized)
- **digest_type**: "daily", "weekly", "monthly", "alert"
- **change_count**: Number of changes included
- **change_ids**: Array of CI_CHANGE_LOG IDs included
- **sent_at**: Timestamp
- **delivery_status**: "sent", "delivered", "bounced", "failed"
- **resend_message_id**: Resend API message ID for tracking
- **subject**: Email subject line
- **html_preview**: First 500 chars of HTML content
- **opened_at**: Timestamp if email was opened (via tracking pixel)
- **clicked_at**: Timestamp if links were clicked

### CI_ENTITY_SNAPSHOTS
Daily snapshots of entity state for change detection comparison:
- **entity_type**: "drug", "trial", "score", "target"
- **entity_id**: Entity identifier (UUID or string)
- **snapshot_data**: JSONB blob of key fields to compare
- **snapshot_date**: Date of snapshot
- Unique constraint: (entity_type, entity_id, snapshot_date)

ETL script `34_detect_changes.py` compares today's entity state against the most recent snapshot to detect changes. New snapshots are saved after each run.
