# Epigenetics Oncology Drug Intelligence - Comprehensive Analysis Report

**Analysis Date**: 2025-11-29
**Database**: Supabase (PostgreSQL)
**Total Records**: 253 across 8 core tables

---

## Executive Summary

This analysis examines a curated dataset of **22 epigenetic drugs** (13 FDA-approved, 9 pipeline) targeting **68 epigenetic proteins** across **30 oncology indications**. The dataset includes comprehensive scoring data (BioScore, ChemScore, TractabilityScore) for **46 drug-indication pairs**.

**Key Findings**:
- **IDH inhibitors** dominate with highest scores (avg 66.1) - clear market leaders
- **HDAC space is saturated** with 36 drug-indication pairs but low differentiation (avg score 44.9)
- **Under-explored opportunities** exist in DNMT, EZH2, BET, and Menin targets
- **Pure-play epigenetics companies** represent 38% of the market (9/24), mostly private

---

## 1. Dataset Overview

### Record Counts by Table

| Table | Record Count | Description |
|-------|--------------|-------------|
| `epi_drugs` | 22 | Epigenetic drugs (small molecules) |
| `epi_targets` | 68 | Epigenetic targets (writers/readers/erasers) |
| `epi_indications` | 30 | Oncology indications with EFO IDs |
| `epi_drug_targets` | 86 | Drug-target relationships |
| `epi_drug_indications` | 46 | Drug-indication links |
| `epi_scores` | 46 | Comprehensive scoring data |
| `epi_companies` | 24 | Companies (16 public, 8 private) |
| `chembl_metrics` | 31 | Chemistry potency/selectivity data |

### Data Completeness

**Drugs Table**:
- Total Drugs: 22
- FDA Approved: 13 (59.1%)
- Pipeline: 9 (40.9%)
- With ChEMBL ID: 22 (100%)
- With Approval Year: 0 (0%) ⚠️ **Data Gap**

**Scores Table**:
- Total Score Records: 46
- With BioScore: 46 (100%)
- With ChemScore: 46 (100%)
- With TractabilityScore: 46 (100%)
- With TotalScore: 46 (100%)

---

## 2. Drug Analysis

### FDA Approved vs Pipeline

| Status | Count | Percentage | Avg TotalScore |
|--------|-------|------------|----------------|
| FDA Approved | 13 | 59.1% | 51.2 |
| Pipeline | 9 | 40.9% | 43.6 |

**Insight**: FDA-approved drugs score 7.6 points higher on average, suggesting the scoring model correlates with clinical success.

### Top 10 Drugs by Average TotalScore

| Rank | Drug | Avg Score | Indications | Status |
|------|------|-----------|-------------|--------|
| 1 | VORASIDENIB | 69.5 | 1 | FDA |
| 2 | OLUTASIDENIB | 66.0 | 1 | FDA |
| 3 | ENASIDENIB | 65.9 | 1 | FDA |
| 4 | IVOSIDENIB | 63.0 | 1 | FDA |
| 5 | AZACITIDINE | 60.0 | 1 | FDA |
| 6 | DECITABINE | 57.0 | 1 | FDA |
| 7 | PANOBINOSTAT | 55.9 | 1 | FDA |
| 8 | QUISINOSTAT | 52.0 | 3 | Pipeline |
| 9 | TACEDINALINE | 50.0 | 3 | Pipeline |
| 10 | ENTINOSTAT | 48.9 | 5 | Pipeline |

**Notable**: Top 7 are all FDA-approved. First pipeline drug (QUISINOSTAT) ranks 8th with a respectable 52.0 score.

### Score Distribution

**Summary Statistics** (46 drug-indication pairs):
- Mean: 45.7
- Median: 44.5
- Std Dev: 12.3
- Min: 18.0
- Max: 69.5

**Histogram**:
```
  0-20:  █ (2.2%)
 20-40:  ███████████████ (30.4%)
 40-60:  █████████████████████████ (50.0%)
 60-80:  ████████ (17.4%)
 80-100: (0.0%)
```

**Insight**: 50% of assets cluster in the 40-60 range. No assets exceed 80, suggesting room for innovation.

---

## 3. Target Analysis

### Target Family Distribution (68 Targets)

| Family | Count | Percentage | Avg TotalScore |
|--------|-------|------------|----------------|
| HDAC | 11 | 16.2% | 44.9 |
| HMT | 11 | 16.2% | 29.0 |
| KDM | 9 | 13.2% | 24.3 |
| SIRT | 7 | 10.3% | — |
| DNMT | 4 | 5.9% | 58.5 |
| BET | 4 | 5.9% | 18.0 |
| PRC2 | 4 | 5.9% | — |
| IDH | 2 | 2.9% | 66.1 |
| Menin | 1 | 1.5% | 36.2 |

**Key Insight**: IDH (2 targets) has the highest avg score (66.1) despite small family size. DNMT also strong (58.5).

### Target Class Distribution

| Class | Count | Percentage |
|-------|-------|------------|
| Eraser | 30 | 44.1% |
| Writer | 17 | 25.0% |
| Core Subunit | 10 | 14.7% |
| Reader | 4 | 5.9% |
| Scaffold | 4 | 5.9% |
| Metabolic Epigenetic | 2 | 2.9% |

**Insight**: Erasers dominate (44.1%), reflecting focus on reversing cancer epigenetics.

### Top 15 Most Targeted Proteins

| Rank | Symbol | Family | Class | Drug Count |
|------|--------|--------|-------|------------|
| 1 | HDAC1 | HDAC | eraser | 12 |
| 2 | HDAC11 | HDAC | eraser | 7 |
| 3 | HDAC8 | HDAC | eraser | 7 |
| 4 | HDAC2 | HDAC | eraser | 7 |
| 5 | HDAC3 | HDAC | eraser | 7 |
| 6 | HDAC6 | HDAC | eraser | 6 |
| 7-11 | HDAC4/5/7/9/10 | HDAC | eraser | 6 each |
| 12 | IDH1 | IDH | metabolic | 3 |
| 13 | DNMT1 | DNMT | writer | 2 |
| 14 | BRD4 | BET | reader | 1 |
| 15 | MEN1 | Menin | scaffold | 1 |

**Insight**: HDAC targets dominate top 11 spots, but with lower scores (44.9 avg). IDH1 (only 3 drugs) punches above weight with 66.1 avg score.

---

## 4. Indication Analysis

### Top 15 Indications by Drug Count

| Rank | Indication | Drug Count |
|------|------------|------------|
| 1 | Acute myeloid leukemia | 5 |
| 2 | Myelodysplastic syndromes | 4 |
| 3 | Hodgkins lymphoma | 3 |
| 4 | Cutaneous T-cell lymphoma | 3 |
| 5 | Peripheral T-cell lymphoma | 2 |
| 6 | Multiple myeloma | 2 |
| 7 | Neoplasm | 2 |
| 8 | Diffuse large B-cell lymphoma | 2 |
| 9 | Lymphoma | 2 |
| 10+ | Single-drug indications | 1 each |

**Insight**: Hematological malignancies dominate. AML and MDS are most pursued.

### Top 10 Best-Scoring Drug-Indication Pairs

| Rank | Drug | Indication | Total | Bio | Chem | Tract |
|------|------|------------|-------|-----|------|-------|
| 1 | VORASIDENIB | Low-grade glioma | 69.5 | 80.9 | 30.0 | 100.0 |
| 2 | CUDC-101 | Neoplasm | 67.4 | 76.7 | 30.0 | 100.0 |
| 3 | ENTINOSTAT | Neoplasm | 67.4 | 76.7 | 30.0 | 100.0 |
| 4 | OLUTASIDENIB | AML | 66.0 | 73.9 | 30.0 | 100.0 |
| 5 | ENASIDENIB | AML | 65.9 | 73.8 | 30.0 | 100.0 |
| 6 | IVOSIDENIB | AML | 63.0 | 73.9 | 20.0 | 100.0 |
| 7 | QUISINOSTAT | Lymphoma | 61.3 | 64.7 | 30.0 | 100.0 |
| 8 | FIMEPINOSTAT | Lymphoma | 61.3 | 64.7 | 30.0 | 100.0 |
| 9 | AZACITIDINE | MDS | 60.0 | 62.0 | 30.0 | 100.0 |
| 10 | TACEDINALINE | Multiple myeloma | 57.7 | 57.5 | 30.0 | 100.0 |

**Insight**: Low-grade glioma (VORASIDENIB) is the highest-scoring pair. All top 10 have perfect TractabilityScore (100.0).

### Top 10 Indications by Average BioScore

| Rank | Indication | Avg BioScore | Drug Count |
|------|------------|--------------|------------|
| 1 | Low-grade glioma | 80.9 | 1 |
| 2 | Neoplasm | 76.7 | 2 |
| 3 | Lymphoma | 64.7 | 2 |
| 4 | Multiple myeloma | 55.6 | 2 |
| 5 | Acute myeloid leukemia | 54.4 | 5 |
| 6 | Breast cancer | 44.4 | 1 |
| 7 | Lung cancer | 42.0 | 1 |
| 8 | Acute leukemia with KMT2A rearrangement | 40.3 | 1 |
| 9 | Cancer | 40.0 | 1 |
| 10 | Myelodysplastic syndromes | 36.9 | 4 |

**Insight**: Glioma and broad "neoplasm" have strongest biological validation. Hematological malignancies follow.

---

## 5. Company Analysis

### Company Portfolio Types

| Type | Count | Percentage |
|------|-------|------------|
| Pure-play Epigenetics | 9 | 37.5% |
| Diversified | 15 | 62.5% |

| Listing Status | Count |
|----------------|-------|
| Public (traded) | 16 |
| Private | 8 |

### Top 15 Companies by Epigenetics Focus Score

| Rank | Company | Ticker | Focus | Pure-Play |
|------|---------|--------|-------|-----------|
| 1 | Omega Therapeutics | OMGA | 100 | Yes |
| 2 | Tune Therapeutics | Private | 100 | Yes |
| 3 | Epicrispr Biotechnologies | Private | 100 | Yes |
| 4 | Chroma Medicine | Private | 100 | Yes |
| 5 | Constellation Pharmaceuticals | Private | 100 | Yes |
| 6 | Oryzon Genomics | ORY | 95 | Yes |
| 7 | Prelude Therapeutics | PRLD | 95 | Yes |
| 8 | Chipscreen Biosciences | Private | 90 | Yes |
| 9 | Forma Therapeutics | Private | 85 | Yes |
| 10 | Agios Pharmaceuticals | AGIO | 70 | No |
| 11 | Verve Therapeutics | VERV | 60 | No |
| 12 | Curis | CRIS | 60 | No |
| 13 | Syndax Pharmaceuticals | SNDX | 50 | No |
| 14 | Xynomic Pharma | Private | 50 | No |
| 15 | Spectrum Pharmaceuticals | SPPI | 40 | No |

**Insight**: Top 5 pure-plays are all 100% focused. 5/9 pure-plays are private, suggesting early-stage market.

---

## 6. Score Insights

### Component Correlations

| Comparison | Pearson Correlation |
|------------|---------------------|
| Bio vs Chem | 0.116 (weak) |
| Bio vs Tract | 0.129 (weak) |
| Chem vs Tract | 0.905 (strong) |

**Insight**: Chemistry and tractability are highly correlated (0.905), as expected. Biology is independent, suggesting biological validation doesn't predict druggability.

### Score Breakdown by Approval Status

| Metric | FDA Approved | Pipeline | Δ |
|--------|--------------|----------|---|
| Total Score | 51.2 | 43.6 | +7.6 |
| Bio Score | 47.3 | 30.5 | +16.8 |
| Chem Score | 26.2 | 28.2 | -2.0 |

**Insight**: FDA drugs have significantly higher BioScore (+16.8), not ChemScore. Validates 50% weighting of BioScore in TotalScore formula.

### Outlier Analysis

#### High Tractability (≥90) but Low Biology (<30): 19 cases

| Drug | BioScore | TractScore | TotalScore |
|------|----------|------------|------------|
| TUCIDINOSTAT | 13.8 | 100.0 | 35.9 |
| TAZEMETOSTAT | 0.0 | 100.0 | 29.0 |
| TACEDINALINE | 26.9 | 100.0 | 42.4 |
| FIMEPINOSTAT | 25.8 | 100.0 | 41.9 |

**Insight**: 19 cases of "druggable but unvalidated" targets. These represent high-risk, high-reward bets.

#### High Biology (≥60) but Low Chemistry (<30): 2 cases

| Drug | BioScore | ChemScore | TotalScore |
|------|----------|-----------|------------|
| DECITABINE | 62.0 | 20.0 | 57.0 |
| IVOSIDENIB | 73.9 | 20.0 | 63.0 |

**Insight**: Only 2 cases of strong biology with weak chemistry. Suggests most validated targets have reasonable chemical matter.

---

## 7. Top Investment Opportunities

**High-Scoring Pipeline Assets (Not Yet FDA Approved)**

| Drug | Indication | Total | Bio | Chem | Tract |
|------|------------|-------|-----|------|-------|
| CUDC-101 | Neoplasm | 67.4 | 76.7 | 30.0 | 100.0 |
| ENTINOSTAT | Neoplasm | 67.4 | 76.7 | 30.0 | 100.0 |
| QUISINOSTAT | Lymphoma | 61.3 | 64.7 | 30.0 | 100.0 |
| FIMEPINOSTAT | Lymphoma | 61.3 | 64.7 | 30.0 | 100.0 |
| TACEDINALINE | Multiple myeloma | 57.7 | 57.5 | 30.0 | 100.0 |
| ENTINOSTAT | Breast cancer | 51.2 | 44.4 | 30.0 | 100.0 |
| TACEDINALINE | Lung cancer | 50.0 | 42.0 | 30.0 | 100.0 |

**Investment Thesis**:
- **CUDC-101 & ENTINOSTAT** for broad neoplasm: 67.4 TotalScore matches best FDA drugs
- **QUISINOSTAT & FIMEPINOSTAT** for lymphoma: 61.3 score, well-validated indication
- All have perfect TractabilityScore (100.0), reducing development risk

---

## 8. Under-Explored Target Opportunities

**Targets with ≤2 Drugs and High Tractability (≥80)**

| Symbol | Family | Drug Count | Avg Tractability |
|--------|--------|------------|------------------|
| DNMT1 | DNMT | 2 | 100.0 |
| EZH2 | HMT | 1 | 100.0 |
| IDH2 | IDH | 1 | 100.0 |
| BRD4 | BET | 1 | 90.0 |
| KDM1A | KDM | 1 | 90.0 |
| MEN1 | Menin | 1 | 80.0 |

**Strategic Recommendations**:
1. **DNMT1**: Only 2 drugs despite 100.0 tractability. Opportunity for next-gen DNMT inhibitors.
2. **EZH2**: Single drug (TAZEMETOSTAT). Large unmet need in solid tumors.
3. **BRD4**: BET reader with only 1 drug. Earlier BET inhibitors failed due to toxicity—room for selective compounds.
4. **MEN1/Menin**: Scaffolding protein, novel mechanism. Low ChemScore (0.0) suggests early chemistry stage.

---

## 9. Data Quality Issues & Recommendations

### Critical Gaps

1. **Missing Approval Dates**: 0/13 FDA-approved drugs have `first_approval_date` populated
   - **Action**: Backfill from FDA Orange Book or ClinicalTrials.gov

2. **Missing Market Cap**: 24/24 companies missing `market_cap` data
   - **Action**: Pull from yfinance API for public companies

3. **ChEMBL Coverage**: Only 19/22 drugs have ChEMBL metrics
   - **Action**: Investigate 3 missing drugs (likely biologics or non-ChEMBL compounds)

4. **Zero BioScores**: 3 score records have BioScore = 0
   - **Action**: Check if targets lack Open Targets associations for those indications

5. **Zero ChemScores**: 3 score records have ChemScore = 0
   - **Action**: Likely missing ChEMBL data for those drugs

### Enhancement Opportunities

1. **Clinical Trial Data**: Integrate ClinicalTrials.gov for phase/status updates
2. **Patent Expiry**: Add patent expiry dates for competitive intelligence
3. **Resistance Mechanisms**: Track known resistance mutations for each target
4. **Combination Data**: Flag approved/tested drug combinations
5. **SAR Data**: Expand ChEMBL metrics to include ADME properties

---

## 10. Key Strategic Insights

### 1. IDH Inhibitors Are Clear Leaders
- **Avg TotalScore**: 66.1 (highest of any family)
- **4 FDA Approvals**: Vorasidenib, Olutasidenib, Enasidenib, Ivosidenib
- **Strong Bio-Validation**: Glioma (80.9) and AML (73.8) have excellent BioScores
- **Implication**: IDH space is validated but potentially saturated

### 2. HDAC Space Is Crowded But Undifferentiated
- **36 drug-indication pairs** (most of any family)
- **Avg TotalScore**: Only 44.9 (below dataset mean of 45.7)
- **High Tractability**: 100.0 (easy to drug)
- **Weak Biology**: 32.6 BioScore (poor validation)
- **Implication**: Me-too competition without novel biology. Avoid unless differentiated mechanism.

### 3. DNMT Inhibitors Have Untapped Potential
- **Avg TotalScore**: 58.5 (second highest after IDH)
- **Only 2 drugs**: AZACITIDINE, DECITABINE
- **Perfect Tractability**: 100.0
- **Implication**: Opportunity for next-gen DNMT inhibitors with improved selectivity/PK

### 4. Pure-Play Epigenetics Companies Are Early-Stage
- **9 pure-play companies** (38% of market)
- **5/9 are private** (56% private rate)
- **Examples**: Omega (OMGA), Tune, Epicrispr, Chroma, Constellation
- **Implication**: Market is immature, M&A opportunities likely

### 5. Hematological Malignancies Dominate
- **Top 3 indications**: AML (5 drugs), MDS (4 drugs), Hodgkins (3 drugs)
- **Solid Tumors Lagging**: Only glioma (1 drug), breast (1 drug), lung (1 drug)
- **Implication**: Opportunity to expand epigenetic drugs into solid tumors (e.g., EZH2 in sarcoma)

---

## 11. Recommended Next Steps

### For Product/Engineering Team
1. **Backfill Missing Data**:
   - FDA approval dates (from Orange Book)
   - Company market caps (from yfinance)
   - ChEMBL data for 3 missing drugs

2. **Enhance Data Model**:
   - Add `patent_expiry_date` to `epi_drugs`
   - Add `clinical_phase` to `epi_drug_indications`
   - Create `epi_combinations` table for combo therapies

3. **Improve Scoring**:
   - Investigate why HDAC has weak BioScores (may need indication-specific adjustments)
   - Consider penalizing crowded targets (e.g., HDAC1 with 12 drugs)

### For Business/Investment Team
1. **Focus on IDH & DNMT**: Highest-scoring families with clinical validation
2. **Avoid HDAC**: Saturated market, weak biology, low differentiation
3. **Explore Under-Explored Targets**: EZH2, BRD4, KDM1A, Menin
4. **Monitor Pure-Plays**: 5 private companies (Tune, Epicrispr, Chroma, Constellation, Chipscreen) are potential M&A targets

### For Data Science Team
1. **Correlation Analysis**: Why is Chem-Tract correlation so high (0.905)? Investigate if TractabilityScore should be reweighted.
2. **Predictive Modeling**: Build model to predict FDA approval based on score components
3. **Anomaly Detection**: Flag assets with unusual score patterns (e.g., high tract + low bio)

---

## Appendix: Scoring Methodology

**TotalScore Formula**:
```
TotalScore = 0.5 × BioScore + 0.3 × ChemScore + 0.2 × TractabilityScore
```

**Component Definitions**:
- **BioScore** (0-100): Open Targets disease-target association strength
  - Based on genetics, somatic mutations, animal models
- **ChemScore** (0-100): ChEMBL potency and selectivity metrics
  - Potency: pXC50 (higher = better on-target activity)
  - Selectivity: Δp (difference vs off-target)
- **TractabilityScore** (0-100): Druggability from Open Targets/UniProt
  - Small molecule tractability buckets (1-10 scale normalized to 0-100)

**Data Sources**:
- Open Targets Platform (v24.09)
- ChEMBL (v34)
- UniProt (2024_05)
- ClinicalTrials.gov (API v2)

---

**Report Generated**: 2025-11-29
**Analyst**: Claude (Anthropic AI)
**Data Source**: `/Users/mananshah/Dev/pilldreams` (Supabase PostgreSQL)
