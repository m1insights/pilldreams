# Perplexity Fact-Check History

This file documents all fact-check tasks run by the Perplexity agent, including outcomes, scripts created, and data corrections made. The agent should check this file before running fact-checks to avoid duplicate work and to reuse existing scripts.

---

## Task Index

| Date | Task | Scripts Created | Discrepancies Found |
|------|------|-----------------|---------------------|
| 2025-12-02 | Company & Drug Ownership Audit | `40_fix_company_drug_ownership.py` | 7 critical |
| 2025-12-02 | Drug Phase Verification | `41_fix_drug_phases.py` | 21 corrections |
| 2025-12-02 | Drug Indication Verification | `42_fix_drug_indications.py` | 23 corrections |
| 2025-12-02 | Target-Drug Coverage Gaps | `43_add_missing_target_drugs.py` | 50 orphan targets, 7 drugs added |

---

## 2025-12-02: Company & Drug Ownership Audit

### Task Description
Verify company information and drug-company assignments for accuracy against authoritative sources.

### Query
```
check the company information and the assets assigned to them, for accuracy
```

### Sources Used
- FDA Drug Approval Records
- Company Press Releases (SEC Filings)
- Acquisition Announcements

### Discrepancies Found

#### CRITICAL (Incorrect Drug Ownership)

1. **IVOSIDENIB** - Assigned to Agios, actually owned by Servier (acquired April 2021)
2. **VORASIDENIB** - Assigned to Agios, actually owned by Servier (acquired April 2021)
3. **ENASIDENIB** - Assigned to Agios/Gilead, actually owned by Servier with BMS co-promotion
4. **OLUTASIDENIB** - Assigned to Agios/Forma, actually licensed to Rigel Pharmaceuticals (Aug 2022)
5. **BELINOSTAT** - Assigned to Spectrum, actually owned by Acrotech Biopharma (acquired March 2019)
6. **DECITABINE** - Assigned to BMS, actually owned by Otsuka (US) and Janssen (EU/ROW)
7. **PELABRESIB** - Assigned to MorphoSys, now owned by Novartis (acquired MorphoSys May 2024)

#### Company Status Issues

- Forma Therapeutics: Missing acquisition by Novo Nordisk (Oct 2022)
- Gilead: Incorrectly linked to enasidenib (never owned this drug)

### Scripts Created

#### `backend/etl/40_fix_company_drug_ownership.py`

**Purpose**: Fixes drug-company ownership discrepancies

**What it does**:
1. Adds 4 new companies (Servier, Rigel, Acrotech, Otsuka)
2. Clears incorrect drug-company links
3. Creates correct ownership relationships with proper roles
4. Updates company statuses (acquired, acquirer info)
5. Removes incorrect links (e.g., Gilead-enasidenib)

**Run command**:
```bash
python -m backend.etl.40_fix_company_drug_ownership
```

**Output example**:
```
DONE: Fixed 12 drug-company relationships
      Added 4 new companies
```

### Files Modified

| File | Change |
|------|--------|
| `backend/etl/40_fix_company_drug_ownership.py` | Created - fix script |
| `backend/etl/seed_epi_companies.csv` | Updated - corrected ownership data |
| `docs/DATABASE_SCHEMA.md` | Updated - added new company counts and ownership section |

### Database Changes

**Companies Added**:
- Servier (Private, France) - IDH inhibitor owner
- Rigel Pharmaceuticals (RIGL) - Olutasidenib licensee
- Acrotech Biopharma (Private, Aurobindo subsidiary) - Belinostat owner
- Otsuka Pharmaceutical (4578.T) - Decitabine US owner

**Drug-Company Links Fixed**:
| Drug | Old Owner | New Owner | Role |
|------|-----------|-----------|------|
| IVOSIDENIB | Agios | Servier | owner |
| VORASIDENIB | Agios | Servier | owner |
| ENASIDENIB | Agios/Gilead | Servier | owner |
| OLUTASIDENIB | Agios/Forma | Rigel | licensee |
| BELINOSTAT | Spectrum | Acrotech | owner |
| DECITABINE | BMS | Otsuka/Janssen | owner/licensee |
| PELABRESIB | MorphoSys | Novartis | owner |

### Verification Sources

- [Servier Agios Acquisition](https://servier.com/wp-content/uploads/2022/11/servier-completes-acquisition-agios-oncology-business_PR.pdf)
- [Vorasidenib First Approval - Drugs Journal](https://link.springer.com/article/10.1007/s40265-024-02097-2)
- [Otsuka Dacogen Rights](https://www.otsuka-us.com/news/otsuka-acquires-rights-hematological-cancer-treatment-dacogenr-decitabine-eisai-us)
- [Ipsen Epizyme Acquisition](https://www.ipsen.com/press-releases/ipsen-completes-acquisition-of-epizyme-expanding-its-portfolio-in-oncology/)
- [Novartis MorphoSys Acquisition](https://www.novartis.com/news/media-releases/novartis-strengthen-oncology-pipeline-agreement-acquire-morphosys-ag-eur-68-share-or-aggregate-eur-27bn-cash)
- [Acrotech Biopharma Belinostat](https://beleodaq.com/)
- [FDA Revumenib Approval](https://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-revumenib-relapsed-or-refractory-acute-leukemia-kmt2a-translocation)

### Verified Correct (No Changes Needed)

| Company | Drug | Status |
|---------|------|--------|
| Bristol-Myers Squibb | AZACITIDINE | Correct |
| Bristol-Myers Squibb | ROMIDEPSIN | Correct |
| Ipsen | TAZEMETOSTAT | Correct |
| Syndax | REVUMENIB | Correct |
| Syndax | ENTINOSTAT | Correct |
| Merck | VORINOSTAT | Correct |

---

## 2025-12-02: Drug Phase Verification

### Task Description
Verify drug max_phase values against FDA approval status. Ensure that the UI displays the highest phase reached (e.g., Phase 4 for approved drugs takes precedence over ongoing Phase 1 trials for new indications).

### Query
```
double check the phases of our assets. There are assets that have trials in multiple phases. but we likely should be displaying the latest phase (ie. phase 4 takes precedence over displaying phase 1 on the UI if the asset has a phase I trial open)
```

### Sources Used
- FDA Drugs@FDA database
- Drugs.com approval history
- Company press releases
- ClinicalTrials.gov

### Discrepancies Found

#### FDA-Approved Drugs with NULL max_phase (9 drugs)

| Drug | Brand Name | Approval Date | Corrected Phase |
|------|------------|---------------|-----------------|
| INCLISIRAN SODIUM | Leqvio | Dec 2021 | 4 |
| EVOLOCUMAB | Repatha | Aug 2015 | 4 |
| ALIROCUMAB | Praluent | July 2015 | 4 |
| PATISIRAN SODIUM | Onpattro | Aug 2018 | 4 |
| INOTERSEN SODIUM | Tegsedi | Oct 2018 | 4 |
| VUTRISIRAN SODIUM | Amvuttra | June 2022 | 4 |
| TAFAMIDIS MEGLUMINE | Vyndaqel | May 2019 | 4 |
| EPLONTERSEN | Wainua | Dec 2023 | 4 |
| ACORAMIDIS | Attruby | Nov 2024 | 4 |

#### Other Phase Corrections (12 drugs)

| Drug | Old Phase | New Phase | Notes |
|------|-----------|-----------|-------|
| PELABRESIB | 2 | 3 | Phase 3 MANIFEST-2 completed |
| APABETALONE | NULL | 3 | Phase 3 BETonMACE completed |
| JQ1 | NULL | 0 | Research tool, never clinical |
| BOCOCIZUMAB | NULL | 3 | Phase 3 discontinued 2016 |
| REVUSIRAN | NULL | 3 | Phase 3 discontinued 2016 |
| SRT-2104 | NULL | 2 | SIRT1 activator Phase 2 |
| EDIFOLIGIDE SODIUM | NULL | 3 | Phase 3 discontinued |
| RALPANCIZUMAB | NULL | 1 | Discontinued PCSK9 Phase 1 |
| FROVOCIMAB | NULL | 2 | PCSK9 antibody Phase 2 |
| LERODALCIBEP | NULL | 3 | Oral PCSK9 inhibitor Phase 3 |
| ONGERICIMAB | NULL | 2 | PCSK9 antibody Phase 2 |
| TAFOLECIMAB | NULL | 3 | PCSK9 antibody Phase 3 (China) |

### Scripts Created

#### `backend/etl/41_fix_drug_phases.py`

**Purpose**: Fixes drug max_phase values based on FDA approval verification

**What it does**:
1. Updates FDA-approved drugs to max_phase=4 and fda_approved=True
2. Corrects phase values for clinical-stage drugs
3. Sets research tools (JQ1) to phase=0
4. Auto-fixes any drugs with fda_approved=True but max_phase≠4

**Run command**:
```bash
python -m backend.etl.41_fix_drug_phases
```

**Output example**:
```
DONE: Updated 21 drug records
--- Verification: All FDA-approved drugs ---
  ✓ ACORAMIDIS: phase=4
  ✓ ALIROCUMAB: phase=4
  ... (22 total)
```

### Files Modified

| File | Change |
|------|--------|
| `backend/etl/41_fix_drug_phases.py` | Created - phase fix script |
| `docs/DATABASE_SCHEMA.md` | Updated - FDA-approved drug count and phase accuracy section |

### Database Changes

- **21 drugs** had max_phase updated
- **9 drugs** marked as FDA-approved (fda_approved=True)
- Total FDA-approved drugs: **22** (was 14)

### Verification Sources

- [Leqvio (Inclisiran) FDA Approval History](https://www.drugs.com/history/leqvio.html)
- [Repatha (Evolocumab) FDA Approval History](https://www.drugs.com/history/repatha.html)
- [Praluent (Alirocumab) FDA Approval](https://pmc.ncbi.nlm.nih.gov/articles/PMC5013849/)
- [Onpattro (Patisiran) FDA Approval](https://investors.alnylam.com/press-release?id=22946)
- [Tegsedi (Inotersen) FDA Approval](https://www.drugs.com/history/tegsedi.html)
- [Amvuttra (Vutrisiran) FDA Approval](https://www.drugs.com/history/amvuttra.html)
- [Vyndaqel (Tafamidis) FDA Approval](https://www.drugs.com/history/vyndaqel.html)
- [Wainua (Eplontersen) FDA Approval](https://www.drugs.com/history/wainua.html)
- [Attruby (Acoramidis) FDA Approval](https://www.fda.gov/drugs/news-events-human-drugs/fda-approves-drug-heart-disorder-caused-transthyretin-mediated-amyloidosis)
- [Pelabresib Phase 3 MANIFEST-2](https://www.nature.com/articles/s41591-025-03572-3)

### Files Deleted (Cleanup)
None - all scripts are reusable.

---

## 2025-12-02: Drug Indication Verification

### Task Description
Verify drug-indication relationships are correct. Ensure FDA-approved drugs have proper indication links, including for PCSK9 inhibitors (hypercholesterolemia) and TTR drugs (ATTR amyloidosis subtypes).

### Query
```
we need to ensure our indications for all drugs in the database are correct. including for combinations.
```

### Sources Used
- FDA Drugs@FDA database
- NCBI StatPearls (PCSK9 Inhibitors)
- Medscape TTR Amyloidosis Treatment Guide
- PMC Disease-modifying therapies for ATTR-CM

### Discrepancies Found

#### FDA-Approved Drugs with NO INDICATIONS LINKED (8 drugs)

| Drug | Brand Name | Drug Class | FDA-Approved Indication |
|------|------------|------------|-------------------------|
| ALIROCUMAB | Praluent | PCSK9 inhibitor | HeFH, ASCVD |
| EVOLOCUMAB | Repatha | PCSK9 inhibitor | HeFH, HoFH, ASCVD |
| INCLISIRAN SODIUM | Leqvio | PCSK9 siRNA | HeFH, ASCVD |
| TAFAMIDIS MEGLUMINE | Vyndaqel | TTR stabilizer | ATTR-CM |
| ACORAMIDIS | Attruby | TTR stabilizer | ATTR-CM |
| PATISIRAN SODIUM | Onpattro | TTR siRNA | hATTR-PN |
| VUTRISIRAN SODIUM | Amvuttra | TTR siRNA | hATTR-PN, ATTR-CM |
| INOTERSEN SODIUM | Tegsedi | TTR ASO | hATTR-PN |
| EPLONTERSEN | Wainua | TTR ASO | hATTR-PN |

#### Combination Therapy Indications (25 combos)
Verified correct - all 25 combination therapy entries have appropriate indication links (oncology focus).

### Scripts Created

#### `backend/etl/42_fix_drug_indications.py`

**Purpose**: Fixes drug-indication relationships based on FDA approval verification

**What it does**:
1. Creates 5 new indications (ATTR Cardiomyopathy, Hereditary ATTR Polyneuropathy, HeFH, HoFH, ASCVD)
2. Links PCSK9 inhibitors to hypercholesterolemia and ASCVD indications
3. Links TTR drugs to appropriate ATTR amyloidosis subtypes
4. Sets approval_status="approved" for all FDA-approved drug-indication pairs

**Run command**:
```bash
python -m backend.etl.42_fix_drug_indications
```

**Output example**:
```
DONE: Added 23 drug-indication links
      Skipped 0 (already existed)
--- Verification: FDA-Approved Drugs with Indications ---
  ✓ ALIROCUMAB: 3 indications
  ✓ EVOLOCUMAB: 4 indications
  ✓ VUTRISIRAN SODIUM: 3 indications
  ... (8 total)
```

### Files Modified

| File | Change |
|------|--------|
| `backend/etl/42_fix_drug_indications.py` | Created - indication fix script |
| `docs/PERPLEXITY_HISTORY.md` | Updated - added this entry |

### Database Changes

**Indications Added (5)**:
- ATTR Cardiomyopathy (Orphanet_85451) - Cardiology
- Hereditary ATTR Polyneuropathy (Orphanet_85447) - Neurology
- Heterozygous Familial Hypercholesterolemia (EFO_0004798) - Cardiology
- Homozygous Familial Hypercholesterolemia (EFO_0004799) - Cardiology
- ASCVD (EFO_0000378) - Cardiology

**Drug-Indication Links Added (23)**:

| Drug | Indications Added |
|------|-------------------|
| ALIROCUMAB | Hypercholesterolemia, HeFH, ASCVD |
| EVOLOCUMAB | Hypercholesterolemia, HeFH, HoFH, ASCVD |
| INCLISIRAN SODIUM | Hypercholesterolemia, HeFH, ASCVD |
| TAFAMIDIS MEGLUMINE | ATTR Amyloidosis, ATTR Cardiomyopathy |
| ACORAMIDIS | ATTR Amyloidosis, ATTR Cardiomyopathy |
| PATISIRAN SODIUM | ATTR Amyloidosis, hATTR Polyneuropathy |
| VUTRISIRAN SODIUM | ATTR Amyloidosis, hATTR Polyneuropathy, ATTR Cardiomyopathy |
| INOTERSEN SODIUM | ATTR Amyloidosis, hATTR Polyneuropathy |
| EPLONTERSEN | ATTR Amyloidosis, hATTR Polyneuropathy |

- Total indications: **38 → 43**
- Total drug-indication pairs: **80 → 103**

### Verification Sources

- [PCSK9 Inhibitors - StatPearls](https://www.ncbi.nlm.nih.gov/books/NBK448100/)
- [Disease‐modifying therapies for ATTR-CM - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11823349/)
- [FDA Approval Vutrisiran for ATTR-CM](https://www.healio.com/news/cardiology/20250321/fda-approves-vutrisiran-for-attr-amyloidosis-with-cardiomyopathy)
- [FDA Approves Acoramidis (Attruby)](https://www.fda.gov/drugs/news-events-human-drugs/fda-approves-drug-heart-disorder-caused-transthyretin-mediated-amyloidosis)
- [Transthyretin Amyloid Cardiomyopathy 2025 Update - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12250813/)

### Verified Correct (No Changes Needed)

All 25 combination therapy entries (epi_combos) have appropriate oncology indication links. The epigenetic oncology drugs also have correct indication mappings.

### Files Deleted (Cleanup)
None - all scripts are reusable.

---

## 2025-12-02: Target-Drug Coverage Gaps

### Task Description
Audit all 79 epigenetic targets to identify which ones have no associated drugs in the database, and add missing clinical-stage drugs for orphan targets.

### Query
```
check all of our targets to see if we arent missing any drugs for them. for example, many targets dont have any drugs associated with them in our database.
```

### Sources Used
- PubMed clinical trial publications
- ClinicalTrials.gov
- NCI Drug Dictionary
- Company press releases
- Chemical Probes Portal

### Analysis Summary

**Initial State:**
- Total targets: 79
- Targets WITH drugs: 29 (37%)
- Targets WITHOUT drugs: 50 (63%)

**Orphan Targets by Family:**
| Family | Count | Notable Targets |
|--------|-------|-----------------|
| HMT | 9 | EHMT2, NSD1, NSD2, NSD3, SMYD3, SUV39H1/2 |
| KDM | 8 | KDM4A/B/C, KDM5A/B/C, KDM6A/B |
| SIRT | 6 | SIRT2, SIRT3, SIRT4, SIRT5, SIRT6, SIRT7 |
| PRC2 | 4 | EED, RBBP4, RBBP7, SUZ12 |
| MuvB | 4 | LIN37, LIN52, LIN54, LIN9 |
| TET | 3 | TET1, TET2, TET3 |
| HAT | 2 | EP300, KAT2A |
| DNMT | 2 | DNMT3B, DNMT3L |
| DP | 2 | TFDP1, TFDP2 |
| Other | 10 | Various |

### Drugs Added

| Drug | Target | Phase | Mechanism | Notes |
|------|--------|-------|-----------|-------|
| INOBRODIB | EP300 | 2 | Bromodomain inhibitor | CellCentric - AML, myeloma, prostate |
| SELISISTAT | (SIRT1)* | 3 | SIRT1 inhibitor | Phase 3 Huntington's, preclinical cancer |
| UNC0642 | EHMT2 | 0 | G9a/GLP inhibitor | Research tool with improved PK |
| GSK-J4 | KDM6A, KDM6B | 0 | KDM6A/B dual inhibitor | Preclinical for AML, CRC |
| KTX-1001 | NSD2 | 1 | NSD2 inhibitor | Phase 1 for relapsed myeloma |
| QC6352 | KDM4A/B/C | 0 | KDM4 inhibitor | Celgene - preclinical renal cancer |
| GSK3368715 | PRMT1 | 1 | Type I PRMT inhibitor | Phase 1 terminated (TEEs) |

*SIRT1 is not in our targets list - only SIRT2-7 are tracked.

### Existing Drug Updated

| Drug | Target Added | Notes |
|------|--------------|-------|
| VALEMETOSTAT | EZH1 | Dual EZH1/2 inhibitor - was only linked to EZH2 |

### Scripts Created

#### `backend/etl/43_add_missing_target_drugs.py`

**Purpose**: Adds missing drugs for orphan targets based on literature research

**What it does**:
1. Adds 7 new drugs with ChEMBL IDs and phase information
2. Creates drug-target links for orphan targets
3. Updates existing drugs with missing target links (VALEMETOSTAT→EZH1)

**Run command**:
```bash
python -m backend.etl.43_add_missing_target_drugs
```

**Output example**:
```
DONE: Added 7 new drugs
      Added 10 drug-target links
--- Verification: Previously Orphan Targets ---
  ✓ EP300: 1 drugs - INOBRODIB
  ✓ EHMT2: 1 drugs - UNC0642
  ✓ KDM6A: 1 drugs - GSK-J4
  ✓ KDM6B: 1 drugs - GSK-J4
  ✓ NSD2: 1 drugs - KTX-1001
```

### Database Changes

**Final State:**
- Total drugs: 60 → **67**
- Drug-target links: 142 → **152**
- Targets WITH drugs: 29 → **39** (49%)
- Targets WITHOUT drugs: 50 → **40** (51%)

**Improvement:** 10 previously orphan targets now have at least one drug linked.

### Verification Sources

- [Inobrodib (CCS1477) - CellCentric](https://www.cellcentric.com/inobrodib/)
- [Selisistat (EX-527) - NCBI](https://pmc.ncbi.nlm.nih.gov/articles/PMC7241506/)
- [GSK-J4 - Chemical Probes Portal](https://www.chemicalprobes.org/gsk-j4)
- [KTX-1001 - NSD2 Inhibitors Review](https://pmc.ncbi.nlm.nih.gov/articles/PMC11092389/)
- [QC6352 - KDM4 Inhibitors Review](https://pmc.ncbi.nlm.nih.gov/articles/PMC9531573/)
- [GSK3368715 - NCI Drug Dictionary](https://www.cancer.gov/publications/dictionaries/cancer-drug/def/prmt1-inhibitor-gsk3368715)
- [Valemetostat - Daiichi Sankyo](https://www.cancer-research-network.com/2024/03/22/valemetostat-ds-3201-is-a-first-in-class-ezh1-2-dual-inhibitor-for-adult-t-cell-leukemia-research/)

### Remaining Orphan Targets (40)

These targets have no associated drugs in the database. Many are challenging to drug or lack clinical-stage inhibitors:

**PRC2 Components**: EED, RBBP4, RBBP7, SUZ12
**MuvB/DREAM**: LIN37, LIN52, LIN54, LIN9, RBL1, RBL2, TFDP1, TFDP2
**DNA Methylation**: DNMT3B, DNMT3L, TET1, TET2, TET3
**HMTs**: EZH1*, NSD1, NSD3, SETD2, SMYD3, SUV39H1, SUV39H2
**KDMs**: KDM4D, KDM5A, KDM5B, KDM5C
**SIRTs**: SIRT2-SIRT7
**HATs**: KAT2A
**Other**: ASXL1, DUX4, MYC, H2AFY, YTHDF1, METTL7A

*EZH1 now has VALEMETOSTAT linked

### Files Deleted (Cleanup)
None - all scripts are reusable.

---

## Agent Instructions

When the Perplexity fact-check agent is called:

1. **Check this file first** - Search for existing entries related to the query
2. **Avoid duplicate work** - If a recent entry exists (< 7 days), summarize findings instead of re-running
3. **Reuse scripts** - If a fix script exists, suggest running it instead of creating a new one
4. **Update this file** - After each task, add a new dated section with:
   - Task description and query
   - Sources consulted
   - Discrepancies found
   - Scripts created (with run commands)
   - Files modified
   - Database changes summary

### Search Patterns

To find relevant history:
- By date: Search `## YYYY-MM-DD`
- By drug: Search drug name (e.g., `IVOSIDENIB`)
- By company: Search company name (e.g., `Servier`)
- By script: Search `.py` extension
- By task type: Search keywords like "ownership", "phase", "acquisition"
