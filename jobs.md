# Data Ingestion Status - pilldreams

## ClinicalTrials.gov Full Ingestion ✅ COMPLETED

**Completed:** 6:00pm EST, Nov 22, 2025 (~3 hours total)

**Final Results:**
- **Compounds:** 26,205 unique drugs
- **Trials:** 28,504 clinical trials (all active Phase 1-3)
- **Drug-Trial Links:** 60,048 interventions
- **Log file:** `full_clinicaltrials_ingestion.log`

---

## ChEMBL Binding Data ✅ COMPLETED

**Status:** 150 drugs processed successfully

**Results:**
- Unique targets: 1,223
- Drug-target bindings: 11,155
- Coverage: 21% of drugs (many don't have ChEMBL IDs)

---

## PubMed Evidence Data ✅ COMPLETED

**Status:** 710 drugs processed successfully

**Results:**
- Drugs with evidence: 354 (50%)
- RCTs indexed: 93,012
- Meta-analyses indexed: 35,240

---

## OpenFDA Safety Data 🔄 RUNNING

**Status:** Still processing (long ingestion ~4-5 hours)

**Expected:**
- Adverse event aggregates for 710 drugs
- MedDRA terms with case counts and PRR scores

---