# Epigenetics Drug Intelligence Database Schema

**Last Updated:** 2025-12-01

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
