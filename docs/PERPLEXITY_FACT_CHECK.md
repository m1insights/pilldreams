# Perplexity Fact-Check Workflow

This document explains how the Perplexity-based fact-checking system works to validate drug, target, and company data.

## Overview

The fact-check system uses Perplexity's `sonar-pro` model to verify our database records against current web sources. This catches:
- **Acquisitions** - Company ownership changes
- **Phase advances** - Clinical trial progress (Phase 2 → 3)
- **New approvals** - FDA/EMA approvals for new indications
- **Discontinued programs** - Failed trials or terminated development
- **Licensing deals** - Partnership changes

## API Pricing

| Service | Pricing | Notes |
|---------|---------|-------|
| **Perplexity sonar-pro** | ~$5 per 1,000 requests | Best accuracy, includes citations |
| **Perplexity sonar** | ~$1 per 1,000 requests | Faster, less comprehensive |

**Cost estimate for pilldreams:**
- 66 drugs × weekly checks = 264 requests/month = ~$1.32/month
- 79 targets × monthly checks = 79 requests/month = ~$0.40/month
- **Total: ~$2/month** for comprehensive fact-checking

## How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                      FACT-CHECK FLOW                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. TRIGGER                                                          │
│     ┌──────────────────────────────────────────────────────────┐    │
│     │ Manual:  POST /ai/fact-check/drug {"drug_id": "uuid"}    │    │
│     │ Batch:   python -m backend.etl.40_batch_fact_check       │    │
│     │ Auto:    After ETL imports new drugs                     │    │
│     └──────────────────────────────────────────────────────────┘    │
│                              │                                       │
│                              ▼                                       │
│  2. BUILD QUERY                                                      │
│     ┌──────────────────────────────────────────────────────────┐    │
│     │ Pull from our database:                                   │    │
│     │ • Drug name: TAZEMETOSTAT                                │    │
│     │ • Company: Ipsen                                         │    │
│     │ • Phase: 4 (Approved)                                    │    │
│     │ • Indications: Follicular lymphoma, Epithelioid sarcoma  │    │
│     │ • Target: EZH2                                           │    │
│     │ • ChEMBL ID: CHEMBL3545110                              │    │
│     └──────────────────────────────────────────────────────────┘    │
│                              │                                       │
│                              ▼                                       │
│  3. CALL PERPLEXITY API                                             │
│     ┌──────────────────────────────────────────────────────────┐    │
│     │ Model: sonar-pro                                         │    │
│     │ Temperature: 0.1 (low for accuracy)                      │    │
│     │ Recency filter: "month" (focus on recent info)           │    │
│     │                                                          │    │
│     │ Prompt:                                                  │    │
│     │ "Verify the following about TAZEMETOSTAT:                │    │
│     │  - Current owner/developer company?                      │    │
│     │  - Approved indications and dates?                       │    │
│     │  - Highest clinical trial phase?                         │    │
│     │  - Any recent acquisitions, licensing, or failures?"     │    │
│     └──────────────────────────────────────────────────────────┘    │
│                              │                                       │
│                              ▼                                       │
│  4. PARSE RESPONSE                                                   │
│     ┌──────────────────────────────────────────────────────────┐    │
│     │ Perplexity returns JSON:                                 │    │
│     │ {                                                        │    │
│     │   "verified_company": "Ipsen",                           │    │
│     │   "verified_phase": 4,                                   │    │
│     │   "verified_indications": [                              │    │
│     │     "Follicular lymphoma",                               │    │
│     │     "Epithelioid sarcoma",                               │    │
│     │     "Endometrial cancer"  ← NEW!                        │    │
│     │   ],                                                     │    │
│     │   "recent_news": "FDA approved for endometrial cancer"   │    │
│     │ }                                                        │    │
│     └──────────────────────────────────────────────────────────┘    │
│                              │                                       │
│                              ▼                                       │
│  5. DIFF & FLAG                                                      │
│     ┌──────────────────────────────────────────────────────────┐    │
│     │ Compare our data vs verified data:                       │    │
│     │                                                          │    │
│     │ ✅ Company: Ipsen (matches)                              │    │
│     │ ✅ Phase: 4 (matches)                                    │    │
│     │ ✅ Target: EZH2 (matches)                                │    │
│     │ ⚠️  Indications: MISMATCH                                │    │
│     │     Ours: ["Follicular lymphoma", "Epithelioid sarcoma"] │    │
│     │     Theirs: + "Endometrial cancer" (new approval 2024)   │    │
│     └──────────────────────────────────────────────────────────┘    │
│                              │                                       │
│                              ▼                                       │
│  6. LOG TO DATABASE                                                  │
│     ┌──────────────────────────────────────────────────────────┐    │
│     │ Table: fact_check_log                                    │    │
│     │ {                                                        │    │
│     │   entity_type: "drug",                                   │    │
│     │   entity_id: "uuid",                                     │    │
│     │   entity_name: "TAZEMETOSTAT",                           │    │
│     │   our_data: {...},                                       │    │
│     │   perplexity_response: {...},                            │    │
│     │   discrepancies: [{field: "indications", ...}],          │    │
│     │   has_discrepancies: true,                               │    │
│     │   status: "pending"                                      │    │
│     │ }                                                        │    │
│     └──────────────────────────────────────────────────────────┘    │
│                              │                                       │
│                              ▼                                       │
│  7. ADMIN REVIEW (in Supabase)                                      │
│     ┌──────────────────────────────────────────────────────────┐    │
│     │ Go to: Supabase → Table Editor → fact_check_log          │    │
│     │ Filter: has_discrepancies = true                         │    │
│     │                                                          │    │
│     │ For each discrepancy:                                    │    │
│     │ • [Confirm] → status = "confirmed" (no action needed)    │    │
│     │ • [Update]  → Update epi_drugs/indications, then         │    │
│     │               status = "updated"                         │    │
│     │ • [Dispute] → status = "disputed" (needs investigation)  │    │
│     └──────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## API Endpoints

### Fact-Check a Drug
```bash
curl -X POST http://localhost:8000/ai/fact-check/drug \
  -H "Content-Type: application/json" \
  -d '{"drug_id": "your-drug-uuid"}'
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
    "target": "EZH2",
    "chembl_id": "CHEMBL3545110"
  },
  "verified_data": {
    "drug_name": "TAZEMETOSTAT",
    "verified_company": "Ipsen (acquired from Epizyme in 2022)",
    "verified_phase": 4,
    "verified_target": "EZH2",
    "verified_indications": [
      "Follicular lymphoma",
      "Epithelioid sarcoma",
      "Endometrial cancer"
    ],
    "approval_status": "approved",
    "recent_news": "FDA approved tazemetostat for endometrial cancer in Jan 2024",
    "confidence": 0.95
  },
  "discrepancies": [
    {
      "field": "indications",
      "ours": ["Follicular lymphoma", "Epithelioid sarcoma"],
      "verified": ["Follicular lymphoma", "Epithelioid sarcoma", "Endometrial cancer"],
      "notes": "New FDA approval in January 2024"
    }
  ],
  "has_discrepancies": true,
  "citations": [
    "https://www.fda.gov/drugs/...",
    "https://www.ipsen.com/..."
  ],
  "checked_at": "2024-12-02T04:55:00Z"
}
```

### Fact-Check a Target
```bash
curl -X POST http://localhost:8000/ai/fact-check/target \
  -H "Content-Type: application/json" \
  -d '{"target_id": "your-target-uuid"}'
```

## What Gets Verified

### For Drugs
| Field | What We Check |
|-------|---------------|
| Company | Current owner (catches acquisitions) |
| Phase | Highest clinical phase (catches advances) |
| Indications | All approved/investigated diseases |
| Target | Primary molecular target |
| Status | approved/clinical/preclinical/discontinued |

### For Targets
| Field | What We Check |
|-------|---------------|
| Name | Full protein name |
| Family | Protein family classification |
| Function | Biological role |
| Drugs | Known drugs targeting this protein |

## Admin Workflow in Supabase

### 1. View Pending Fact-Checks
```
Supabase → Table Editor → fact_check_log
Filter: status = 'pending'
Sort: checked_at DESC
```

### 2. Review Each Discrepancy
For each row with `has_discrepancies = true`:

1. **Read the discrepancy details** in the `discrepancies` column
2. **Check citations** in `perplexity_response` for source URLs
3. **Decide action:**
   - If Perplexity is right → Update our database
   - If we're right → Mark as confirmed
   - If unclear → Mark as disputed for investigation

### 3. Update Status
| Status | Meaning |
|--------|---------|
| `pending` | Needs review |
| `confirmed` | Reviewed, our data is correct |
| `updated` | Updated our database with new info |
| `disputed` | Needs further investigation |

## Batch Fact-Checking

### Manual Batch (Recommended for Now)
```bash
# Get list of drug IDs
curl -s http://localhost:8000/epi/drugs | \
  python3 -c "import sys,json; [print(d['id']) for d in json.load(sys.stdin)[:10]]"

# Fact-check each (loop in shell)
for id in $(cat drug_ids.txt); do
  curl -X POST http://localhost:8000/ai/fact-check/drug \
    -H "Content-Type: application/json" \
    -d "{\"drug_id\": \"$id\"}"
  sleep 2  # Rate limit
done
```

### Future: Automated Batch Script
```bash
# TODO: python -m backend.etl.40_batch_fact_check
# Options:
#   --stale-days 30    Check drugs not verified in 30+ days
#   --limit 10         Only check 10 per run (cost control)
#   --priority approved  Prioritize FDA-approved drugs
```

## Recommended Schedule

| Entity Type | Frequency | Reason |
|-------------|-----------|--------|
| FDA-approved drugs | Weekly | High visibility, catch new approvals |
| Phase 3 drugs | Bi-weekly | Near approval, status changes often |
| Phase 1-2 drugs | Monthly | Lower priority, less news |
| Targets | Quarterly | Rarely change fundamentally |

## Cost Management

**Tips to reduce API costs:**
1. Only check drugs that haven't been verified recently
2. Prioritize high-value drugs (approved, late-stage)
3. Use `--limit` flag in batch scripts
4. Cache results in `fact_check_log` to avoid re-checking

**Estimated monthly cost:**
- Conservative (weekly approved only): ~$0.50/month
- Moderate (all drugs monthly): ~$2/month
- Aggressive (all drugs weekly): ~$8/month

## Environment Setup

```bash
# Required in .env
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxx

# Get your key at: https://www.perplexity.ai/settings/api
```

## Troubleshooting

### "PERPLEXITY_API_KEY not configured"
Set the environment variable in your `.env` file.

### 429 Rate Limit Error
Add delays between requests. Perplexity allows ~100 requests/minute.

### JSON Parsing Errors
The AI sometimes returns malformed JSON. The system logs raw responses for debugging.

### Incorrect Verified Data
Perplexity can be wrong. Always check citations before updating your database.
Mark unclear cases as "disputed" for manual investigation.
