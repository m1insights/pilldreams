# Competitive Intelligence Platform Implementation Plan

**Last Updated:** 2025-12-03 00:15 PST
**Target Persona:** CI Professionals + R&D Strategy Analysts
**Pricing Target:** $20-40K/year

---

## Implementation Progress

| Week | Feature | Status | Completed | Notes |
|------|---------|--------|-----------|-------|
| Week 1 | Trial Calendar Foundation | ✅ **DONE** | 2025-12-02 | 991 trials ingested |
| Week 2 | Change Detection + Digest | ✅ **DONE** | 2025-12-03 | ETL + email template ready |
| Week 3 | PDUFA Tracker | 🔲 Pending | - | Next priority |
| Week 4 | Watchlist + Alerts | 🔲 Pending | - | |
| Week 5 | Exports (PPTX/XLSX) | 🔲 Pending | - | |
| Week 6 | Auth + Payments | 🔲 Pending | - | |

### Completed Work Log

#### 2025-12-02: Trial Calendar Foundation ✅

**Schema Created** (via `core/migration_ctgov_trial_calendar.sql`):
- `ci_trial_calendar` - 991 trials with primary completion dates
- `ci_curated_trials` - Tier 1 curated NCT IDs for PCSK9/TTR drugs
- `ci_conferences` - 8 major oncology conferences seeded for 2025
- `ci_change_log` - Ready for change detection
- Added `ctgov_query_tier` column to `epi_drugs` (tier1_curated: 17, tier2_oncology: 42, skip: 1)

**ETL Script Created** (`backend/etl/32_fetch_trial_dates.py`):
- CT.gov API v2 integration with tiered query strategy
- Tier 1: Curated NCT IDs only (PCSK9, TTR, E2F drugs)
- Tier 2: Drug name + oncology conditions filter
- Upsert logic (insert new, update existing)
- Links trials to epi_drugs table

**Data Ingested**:
| Metric | Value |
|--------|-------|
| Total Trials | 991 |
| Phase 3 | 63 |
| Phase 2 | 355 |
| Phase 1 | 514 |
| Currently Recruiting | 260 |
| Completed | 543 |

**Top Drugs by Trial Count**:
1. VORINOSTAT: 145 trials
2. DECITABINE: 141 trials
3. TUCIDINOSTAT: 103 trials
4. AZACITIDINE: 102 trials
5. PANOBINOSTAT: 79 trials

**Files Created**:
- `core/migration_ctgov_trial_calendar.sql`
- `backend/etl/32_fetch_trial_dates.py`
- `backend/etl/seed_curated_trials.csv`
- `scripts/verify_trial_calendar.py`

#### 2025-12-03: Change Detection + Digest ✅

**Schema Created** (via `core/migration_ci_change_detection.sql`):
- `ci_change_log` - Tracks all entity changes with significance classification
- `ci_user_digest_prefs` - User preferences for digest frequency, filters
- `ci_digest_history` - Audit trail of sent digests
- `ci_entity_snapshots` - Daily snapshots for change comparison
- `log_entity_change()` PostgreSQL function for easy logging

**ETL Scripts Created**:
- `backend/etl/34_detect_changes.py` - Compares snapshots, detects changes
  - Supports drugs, trials, scores entity types
  - Auto-classifies significance (critical/high/medium/low)
  - Dry-run mode for testing
- `backend/etl/35_generate_digest.py` - Generates HTML email digests
  - Professional email template with branded styling
  - Resend API integration for delivery
  - Preview mode generates local HTML file
  - Plain text fallback included

**Significance Rules**:
| Change Type | Significance |
|-------------|--------------|
| Phase 2 → Phase 3 | Critical |
| FDA Approval | Critical |
| Trial Terminated/Completed | High |
| Date Change | Medium |
| Score Change (>10 pts) | Medium |
| Minor Updates | Low |

**Files Created**:
- `core/migration_ci_change_detection.sql`
- `backend/etl/34_detect_changes.py`
- `backend/etl/35_generate_digest.py`

**To Activate**:
1. Run migration in Supabase: `cat core/migration_ci_change_detection.sql | pbcopy`
2. Add `RESEND_API_KEY` to `.env`
3. Run daily: `python -m backend.etl.34_detect_changes`
4. Run weekly: `python -m backend.etl.35_generate_digest`

---

## Executive Summary

This document outlines a 6-week implementation plan for transforming pilldreams from a data browser into an actionable CI platform. The key principle is **automated data maintenance** - every feature must be maintainable with minimal manual intervention.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES (Automated)                      │
├─────────────────────────────────────────────────────────────────────┤
│  ClinicalTrials.gov API  │  FDA RSS/Web  │  News RSS  │  Patents    │
│  (Trial dates, phases)   │  (PDUFA dates) │  (Events)  │  (IP moves) │
└────────────┬─────────────┴───────┬───────┴─────┬──────┴──────┬──────┘
             │                     │             │             │
             ▼                     ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        ETL LAYER (Daily/Weekly Cron)                 │
├─────────────────────────────────────────────────────────────────────┤
│  32_fetch_trial_dates.py   │  33_fetch_pdufa.py  │  30_fetch_news.py │
│  34_detect_changes.py      │  35_generate_digest.py                  │
└────────────┬─────────────────────┬──────────────────────────────────┘
             │                     │
             ▼                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DATABASE (Supabase)                           │
├─────────────────────────────────────────────────────────────────────┤
│  ci_trial_calendar    │  ci_pdufa_dates    │  ci_change_log          │
│  ci_watchlist         │  ci_alerts         │  ci_digest_queue        │
└────────────┬─────────────────────┬──────────────────────────────────┘
             │                     │
             ▼                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        NOTIFICATION LAYER                            │
├─────────────────────────────────────────────────────────────────────┤
│  Email (Resend)  │  Slack (Webhook)  │  In-App (WebSocket)           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Feature 1: Trial Readout Calendar

### Data Sources

| Source | Data Available | Automation Level | Update Frequency |
|--------|---------------|------------------|------------------|
| **ClinicalTrials.gov API v2** | Primary Completion Date, Study Completion Date, Phase, Status | Fully automated | Daily |
| **Company Press Releases** | Conference presentation dates, investor day | LLM-assisted extraction | Daily (RSS) |
| **Conference Calendars** | ASCO, ASH, AACR dates | Semi-annual manual seed | Yearly |

### Database Schema

```sql
-- New table: ci_trial_calendar
CREATE TABLE ci_trial_calendar (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Trial identification
    nct_id TEXT UNIQUE NOT NULL,
    trial_title TEXT,

    -- Dates (the core value)
    primary_completion_date DATE,
    primary_completion_type TEXT,  -- 'Actual' or 'Anticipated'
    study_completion_date DATE,
    study_completion_type TEXT,
    results_first_posted DATE,

    -- Classification
    phase TEXT,  -- 'Phase 1', 'Phase 2', 'Phase 3', 'Phase 4'
    status TEXT,  -- 'Recruiting', 'Active', 'Completed', 'Terminated'

    -- Linkage to our entities
    drug_id UUID REFERENCES epi_drugs(id),
    drug_name TEXT,  -- Denormalized for quick display
    target_ids UUID[],
    indication_id UUID REFERENCES epi_indications(id),
    indication_name TEXT,

    -- Sponsor info
    lead_sponsor TEXT,
    collaborators TEXT[],

    -- Metadata
    source TEXT DEFAULT 'clinicaltrials.gov',
    last_api_update TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_trial_calendar_pcd ON ci_trial_calendar(primary_completion_date);
CREATE INDEX idx_trial_calendar_drug ON ci_trial_calendar(drug_id);
CREATE INDEX idx_trial_calendar_status ON ci_trial_calendar(status);

-- New table: ci_conferences (semi-static)
CREATE TABLE ci_conferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,  -- 'ASCO Annual Meeting'
    short_name TEXT,     -- 'ASCO'
    start_date DATE,
    end_date DATE,
    abstract_deadline DATE,
    location TEXT,
    year INTEGER,
    url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### ETL Script: 32_fetch_trial_dates.py

```python
"""
ETL 32: Fetch Clinical Trial Dates from ClinicalTrials.gov API v2

Queries for all trials matching our epigenetic drugs and targets.
Updates primary_completion_date and study_completion_date.

Automation: Runs daily via cron
Rate Limit: 50 requests/minute (we batch with 3-sec delays)
"""

import requests
from datetime import datetime, timedelta

CTGOV_API = "https://clinicaltrials.gov/api/v2/studies"

# Search for trials matching our drugs
def fetch_trials_for_drug(drug_name: str, chembl_id: str = None):
    """Query CT.gov for trials mentioning this drug."""
    params = {
        "query.intr": drug_name,  # Intervention field
        "filter.overallStatus": "RECRUITING,ACTIVE_NOT_RECRUITING,COMPLETED",
        "fields": "NCTId,BriefTitle,Phase,OverallStatus,PrimaryCompletionDate,PrimaryCompletionDateType,StudyCompletionDate,LeadSponsorName",
        "pageSize": 100,
        "format": "json"
    }

    response = requests.get(CTGOV_API, params=params)
    return response.json().get("studies", [])

def parse_trial(study: dict, drug_id: str) -> dict:
    """Parse CT.gov study into our schema."""
    protocol = study.get("protocolSection", {})
    status_module = protocol.get("statusModule", {})
    id_module = protocol.get("identificationModule", {})
    sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
    design_module = protocol.get("designModule", {})

    pcd = status_module.get("primaryCompletionDateStruct", {})
    scd = status_module.get("completionDateStruct", {})

    return {
        "nct_id": id_module.get("nctId"),
        "trial_title": id_module.get("briefTitle"),
        "primary_completion_date": pcd.get("date"),
        "primary_completion_type": pcd.get("type"),
        "study_completion_date": scd.get("date"),
        "study_completion_type": scd.get("type"),
        "phase": design_module.get("phases", [None])[0],
        "status": status_module.get("overallStatus"),
        "lead_sponsor": sponsor_module.get("leadSponsor", {}).get("name"),
        "drug_id": drug_id,
        "last_api_update": datetime.utcnow().isoformat()
    }
```

### Frontend Component: Calendar View

```tsx
// components/ci/TrialCalendar.tsx
// Display upcoming trial readouts in calendar format
// Features:
// - Month/Week/List view toggle
// - Filter by phase, drug, target, company
// - Color coding: Green=Q1, Yellow=Q2-Q3, Gray=Q4+
// - Click to expand trial details
// - Export to iCal/Google Calendar
```

### Accuracy Maintenance

| Challenge | Solution | Frequency |
|-----------|----------|-----------|
| Dates change frequently | Daily API refresh | Daily 2am |
| New trials added | Query by drug name + target | Daily |
| Trial status changes | Check status field | Daily |
| Missed trials | Quarterly full refresh by NCT ID patterns | Quarterly |

---

## Feature 2: Weekly Change Digest

### Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Daily ETL  │────▶│ Change Log  │────▶│   Digest    │────▶│   Email     │
│  Scripts    │     │   Table     │     │  Generator  │     │  (Resend)   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### Database Schema

```sql
-- Track every change for audit + digest
CREATE TABLE ci_change_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What changed
    entity_type TEXT NOT NULL,  -- 'drug', 'trial', 'company', 'patent', 'news'
    entity_id UUID,
    entity_name TEXT,

    -- Change details
    change_type TEXT NOT NULL,  -- 'phase_change', 'status_change', 'new_entity', 'score_change', 'date_change'
    field_changed TEXT,
    old_value TEXT,
    new_value TEXT,

    -- Significance for alerting
    significance TEXT DEFAULT 'low',  -- 'low', 'medium', 'high', 'critical'

    -- Source
    source TEXT,  -- 'ctgov', 'fda', 'news', 'patent', 'manual'
    source_url TEXT,

    -- Timestamps
    detected_at TIMESTAMPTZ DEFAULT NOW(),

    -- Digest status
    digest_sent BOOLEAN DEFAULT FALSE,
    digest_sent_at TIMESTAMPTZ
);

CREATE INDEX idx_change_log_entity ON ci_change_log(entity_type, entity_id);
CREATE INDEX idx_change_log_significance ON ci_change_log(significance);
CREATE INDEX idx_change_log_digest ON ci_change_log(digest_sent, detected_at);

-- User preferences for digest
CREATE TABLE ci_user_digest_prefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,  -- Supabase Auth user

    -- Frequency
    digest_frequency TEXT DEFAULT 'weekly',  -- 'daily', 'weekly', 'monthly'
    digest_day INTEGER DEFAULT 1,  -- 1=Monday for weekly
    digest_hour INTEGER DEFAULT 9,  -- 9am
    digest_timezone TEXT DEFAULT 'America/New_York',

    -- Filters
    min_significance TEXT DEFAULT 'low',  -- Only include changes >= this level
    entity_types TEXT[] DEFAULT ARRAY['drug', 'trial', 'company'],

    -- Contact
    email TEXT NOT NULL,
    slack_webhook_url TEXT,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_digest_sent TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Significance Classification

| Change Type | Significance | Example |
|-------------|--------------|---------|
| Phase 2 → Phase 3 | **Critical** | "Entinostat advances to Phase 3 in NSCLC" |
| FDA approval | **Critical** | "Tazemetostat approved for epithelioid sarcoma" |
| Trial terminated | **High** | "Phase 2 trial halted for safety" |
| New IND filing | **High** | "Prelude files IND for PRMT5 inhibitor" |
| Completion date change | **Medium** | "Primary completion moved from Q1 to Q3 2025" |
| New patent published | **Medium** | "Vertex files EZH2 combination patent" |
| News mention | **Low** | "Nature article mentions DOT1L research" |
| Score recalculation | **Low** | "BioScore updated from 65 to 68" |

### ETL Script: 34_detect_changes.py

```python
"""
ETL 34: Detect Changes Across All Entities

Compares current database state with previous snapshot.
Logs all changes to ci_change_log with significance classification.

Automation: Runs daily after all other ETLs complete
"""

from datetime import datetime, timedelta
import json

# Significance rules
SIGNIFICANCE_RULES = {
    ("drug", "max_phase", "3→4"): "critical",  # FDA approval
    ("drug", "max_phase", "2→3"): "critical",  # Phase advancement
    ("trial", "status", "→Terminated"): "high",
    ("trial", "status", "→Completed"): "high",
    ("trial", "primary_completion_date", "*"): "medium",
    ("company", "status", "→acquired"): "critical",
    ("patent", "new", "*"): "medium",
    ("news", "ai_impact_flag", "bullish"): "medium",
    ("news", "ai_impact_flag", "bearish"): "high",
}

def classify_significance(entity_type: str, field: str, old_val: str, new_val: str) -> str:
    """Determine significance of a change."""
    change_key = f"{old_val}→{new_val}" if old_val else f"→{new_val}"

    # Check specific rules
    for (e_type, f_name, pattern), sig in SIGNIFICANCE_RULES.items():
        if e_type == entity_type and f_name == field:
            if pattern == "*" or pattern == change_key:
                return sig

    return "low"

def detect_trial_changes(current: dict, previous: dict) -> list:
    """Compare trial records and log changes."""
    changes = []

    # Check date changes
    if current.get("primary_completion_date") != previous.get("primary_completion_date"):
        changes.append({
            "entity_type": "trial",
            "entity_id": current["id"],
            "entity_name": current["nct_id"],
            "change_type": "date_change",
            "field_changed": "primary_completion_date",
            "old_value": previous.get("primary_completion_date"),
            "new_value": current.get("primary_completion_date"),
            "significance": "medium",
            "source": "ctgov"
        })

    # Check status changes
    if current.get("status") != previous.get("status"):
        sig = classify_significance("trial", "status", previous.get("status"), current.get("status"))
        changes.append({
            "entity_type": "trial",
            "entity_id": current["id"],
            "entity_name": current["nct_id"],
            "change_type": "status_change",
            "field_changed": "status",
            "old_value": previous.get("status"),
            "new_value": current.get("status"),
            "significance": sig,
            "source": "ctgov"
        })

    return changes
```

### Digest Email Template

```html
<!-- templates/digest_email.html -->
<h1>Epigenetics Intelligence Weekly Digest</h1>
<p>Week of {{ week_start }} - {{ week_end }}</p>

{% if critical_changes %}
<h2>🚨 Critical Updates</h2>
<ul>
{% for change in critical_changes %}
  <li>
    <strong>{{ change.entity_name }}</strong>: {{ change.change_type }}
    <br>{{ change.old_value }} → {{ change.new_value }}
  </li>
{% endfor %}
</ul>
{% endif %}

{% if high_changes %}
<h2>⚠️ Important Changes</h2>
<!-- ... -->
{% endif %}

<h2>📅 Upcoming Trial Readouts (Next 30 Days)</h2>
<table>
  <tr><th>Date</th><th>Trial</th><th>Drug</th><th>Phase</th></tr>
  {% for trial in upcoming_trials %}
  <tr>
    <td>{{ trial.primary_completion_date }}</td>
    <td>{{ trial.nct_id }}</td>
    <td>{{ trial.drug_name }}</td>
    <td>{{ trial.phase }}</td>
  </tr>
  {% endfor %}
</table>

<h2>📊 Score Changes</h2>
<!-- ... -->
```

---

## Feature 3: PDUFA/Regulatory Tracker

### Data Sources

| Source | Automation Level | Notes |
|--------|------------------|-------|
| FDA Press Releases RSS | Fully automated | New approvals, CRLs |
| SEC 8-K filings | Fully automated (EDGAR API) | Companies announce PDUFA dates |
| Company press releases | LLM-assisted | PDUFA date announcements |
| BioPharmCatalyst | Manual scrape fallback | Comprehensive but no API |

### Database Schema

```sql
CREATE TABLE ci_pdufa_dates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Drug info
    drug_id UUID REFERENCES epi_drugs(id),
    drug_name TEXT NOT NULL,
    applicant TEXT,  -- Company name

    -- Application details
    application_type TEXT,  -- 'NDA', 'BLA', 'sNDA', 'sBLA'
    application_number TEXT,
    indication TEXT,

    -- Key dates
    pdufa_date DATE NOT NULL,
    submission_date DATE,
    priority_review BOOLEAN DEFAULT FALSE,
    breakthrough_therapy BOOLEAN DEFAULT FALSE,
    accelerated_approval BOOLEAN DEFAULT FALSE,

    -- Outcome (updated after decision)
    outcome TEXT,  -- 'approved', 'crl', 'pending'
    outcome_date DATE,
    outcome_notes TEXT,

    -- Source
    source TEXT,
    source_url TEXT,
    confidence TEXT DEFAULT 'confirmed',  -- 'confirmed', 'estimated', 'rumored'

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pdufa_date ON ci_pdufa_dates(pdufa_date);
CREATE INDEX idx_pdufa_drug ON ci_pdufa_dates(drug_id);
```

### ETL Script: 33_fetch_pdufa.py

```python
"""
ETL 33: Fetch PDUFA Dates from Multiple Sources

Sources:
1. FDA RSS feeds (for approvals/CRLs)
2. SEC EDGAR (8-K filings mentioning PDUFA)
3. Company RSS feeds (press releases)
4. Manual curation spreadsheet (Google Sheets)

The LLM (Gemini) extracts PDUFA dates from unstructured text.
Perplexity validates ambiguous dates.

Automation: Daily for RSS, weekly for comprehensive search
"""

import feedparser
import requests
from google import generativeai as genai

# FDA RSS feeds
FDA_RSS_FEEDS = {
    "approvals": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/drug-approvals/rss.xml",
    "press_releases": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml",
}

def extract_pdufa_from_8k(filing_text: str) -> dict:
    """Use Gemini to extract PDUFA date from SEC 8-K filing."""
    prompt = """
    Extract PDUFA date information from this SEC 8-K filing.
    Return JSON with:
    - drug_name: string
    - pdufa_date: YYYY-MM-DD or null
    - indication: string
    - priority_review: boolean
    - confidence: "confirmed" | "estimated"

    Filing text:
    {text}
    """

    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt.format(text=filing_text[:4000]))

    # Parse JSON response with retry logic
    return parse_ai_json(response.text)

def validate_pdufa_with_perplexity(drug_name: str, claimed_date: str) -> dict:
    """Cross-check PDUFA date with Perplexity for validation."""
    # Use Perplexity MCP to verify
    query = f"What is the PDUFA date for {drug_name}? Is it {claimed_date}?"
    # Returns validated date + sources
    pass
```

### Accuracy Maintenance

| Challenge | Solution |
|-----------|----------|
| PDUFA dates not in structured API | LLM extraction from SEC filings + press releases |
| Date changes (FDA extends, CRL resubmission) | Weekly re-validation with Perplexity |
| False positives from LLM | Confidence scoring + manual review queue |
| Missing dates | Fallback to manual curation spreadsheet |

---

## Feature 4: Competitor Watchlist + Alerts

### Database Schema

```sql
-- User's watchlist
CREATE TABLE ci_watchlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,

    -- What they're watching
    entity_type TEXT NOT NULL,  -- 'company', 'drug', 'target', 'indication'
    entity_id UUID NOT NULL,
    entity_name TEXT,  -- Denormalized

    -- Alert preferences
    alert_on_news BOOLEAN DEFAULT TRUE,
    alert_on_trial_update BOOLEAN DEFAULT TRUE,
    alert_on_phase_change BOOLEAN DEFAULT TRUE,
    alert_on_patent BOOLEAN DEFAULT TRUE,
    alert_on_pdufa BOOLEAN DEFAULT TRUE,

    -- Notification channels
    notify_email BOOLEAN DEFAULT TRUE,
    notify_slack BOOLEAN DEFAULT FALSE,
    notify_in_app BOOLEAN DEFAULT TRUE,

    -- Metadata
    added_at TIMESTAMPTZ DEFAULT NOW(),
    last_alert_sent TIMESTAMPTZ
);

CREATE UNIQUE INDEX idx_watchlist_unique ON ci_watchlist(user_id, entity_type, entity_id);

-- Alert history
CREATE TABLE ci_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,

    -- What triggered the alert
    change_log_id UUID REFERENCES ci_change_log(id),
    watchlist_id UUID REFERENCES ci_watchlist(id),

    -- Alert content
    title TEXT NOT NULL,
    body TEXT,
    entity_type TEXT,
    entity_name TEXT,
    significance TEXT,

    -- Delivery status
    email_sent BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMPTZ,
    slack_sent BOOLEAN DEFAULT FALSE,
    in_app_read BOOLEAN DEFAULT FALSE,
    in_app_read_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Real-Time Alert Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Change Log  │────▶│   Matcher    │────▶│   Router     │────▶│  Channels    │
│  Insert      │     │  (Watchlist) │     │  (Prefs)     │     │  (Email/     │
│  Trigger     │     │              │     │              │     │   Slack)     │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Supabase Edge Function: Alert Matcher

```typescript
// supabase/functions/alert-matcher/index.ts
import { createClient } from '@supabase/supabase-js'
import { Resend } from 'resend'

const supabase = createClient(
  Deno.env.get('SUPABASE_URL')!,
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
)
const resend = new Resend(Deno.env.get('RESEND_API_KEY'))

Deno.serve(async (req) => {
  const { record } = await req.json()  // ci_change_log insert

  // Find all users watching this entity
  const { data: watchers } = await supabase
    .from('ci_watchlist')
    .select('*, users(email)')
    .eq('entity_id', record.entity_id)
    .eq('entity_type', record.entity_type)

  for (const watcher of watchers) {
    // Check if this change type triggers alert
    const shouldAlert = checkAlertPrefs(watcher, record)
    if (!shouldAlert) continue

    // Create alert record
    const { data: alert } = await supabase
      .from('ci_alerts')
      .insert({
        user_id: watcher.user_id,
        change_log_id: record.id,
        watchlist_id: watcher.id,
        title: formatAlertTitle(record),
        body: formatAlertBody(record),
        entity_type: record.entity_type,
        entity_name: record.entity_name,
        significance: record.significance
      })
      .select()
      .single()

    // Send email if enabled
    if (watcher.notify_email) {
      await resend.emails.send({
        from: 'alerts@pilldreams.io',
        to: watcher.users.email,
        subject: `[${record.significance.toUpperCase()}] ${formatAlertTitle(record)}`,
        html: renderAlertEmail(alert, record)
      })

      await supabase
        .from('ci_alerts')
        .update({ email_sent: true, email_sent_at: new Date().toISOString() })
        .eq('id', alert.id)
    }

    // Send Slack if enabled
    if (watcher.notify_slack && watcher.slack_webhook_url) {
      await sendSlackAlert(watcher.slack_webhook_url, alert, record)
    }
  }

  return new Response(JSON.stringify({ processed: watchers.length }))
})
```

---

## Feature 5: PowerPoint/Excel Export

### Export Types

| Export | Format | Use Case |
|--------|--------|----------|
| Drug Landscape | PPTX | "All HDAC inhibitors in development" |
| Competitive Matrix | XLSX | "Compare 5 EZH2 inhibitors side-by-side" |
| Company Pipeline | PPTX | "Lilly's epigenetics portfolio" |
| Trial Calendar | XLSX/ICS | "Export upcoming readouts to calendar" |
| Watchlist Report | PDF | "Weekly summary of my tracked assets" |

### Technology Stack

```
Python Backend:
- python-pptx: PowerPoint generation
- openpyxl: Excel generation
- reportlab: PDF generation
- jinja2: Template rendering

Pre-built Templates:
- templates/pptx/drug_landscape.pptx
- templates/pptx/competitive_matrix.pptx
- templates/pptx/company_pipeline.pptx
```

### API Endpoints

```python
# backend/api/exports.py

@router.post("/exports/pptx/drug-landscape")
async def export_drug_landscape(
    target_family: str = "HDAC",
    min_phase: int = 1,
    include_scores: bool = True
) -> FileResponse:
    """Generate PowerPoint deck of drugs targeting a family."""

    # Fetch data
    drugs = await get_drugs_by_target_family(target_family, min_phase)

    # Load template
    prs = Presentation("templates/pptx/drug_landscape.pptx")

    # Populate slides
    title_slide = prs.slides[0]
    title_slide.shapes.title.text = f"{target_family} Inhibitor Landscape"

    # Add drug slides
    for drug in drugs:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        # ... populate with drug data

    # Save and return
    buffer = BytesIO()
    prs.save(buffer)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename={target_family}_landscape.pptx"}
    )

@router.post("/exports/xlsx/competitive-matrix")
async def export_competitive_matrix(
    drug_ids: list[str],
    fields: list[str] = ["phase", "indication", "bio_score", "chem_score", "total_score"]
) -> FileResponse:
    """Generate Excel comparison matrix."""

    drugs = await get_drugs_by_ids(drug_ids)

    wb = Workbook()
    ws = wb.active
    ws.title = "Competitive Matrix"

    # Header row
    headers = ["Drug"] + fields
    ws.append(headers)

    # Data rows
    for drug in drugs:
        row = [drug.name] + [getattr(drug, f) for f in fields]
        ws.append(row)

    # Style
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="1E3A5F")

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return StreamingResponse(buffer, ...)
```

---

## Automation Schedule (Cron Jobs)

| Job | Schedule | Script | Duration |
|-----|----------|--------|----------|
| Trial dates refresh | Daily 2am EST | 32_fetch_trial_dates.py | ~10 min |
| PDUFA dates refresh | Daily 3am EST | 33_fetch_pdufa.py | ~5 min |
| News RSS fetch | Every 4 hours | 30_fetch_news.py | ~5 min |
| Patent fetch | Daily 4am EST | 31_fetch_patents.py | ~15 min |
| Change detection | Daily 5am EST | 34_detect_changes.py | ~5 min |
| Weekly digest | Monday 9am EST | 35_generate_digest.py | ~2 min |
| Perplexity validation | Weekly Sunday | 36_validate_with_perplexity.py | ~30 min |

### Cron Setup (Render / Railway / Local)

```bash
# crontab -e
# Pilldreams CI Platform ETL Jobs

# Trial dates - daily 2am EST
0 7 * * * cd /app && python -m backend.etl.32_fetch_trial_dates >> /var/log/etl/trial_dates.log 2>&1

# PDUFA dates - daily 3am EST
0 8 * * * cd /app && python -m backend.etl.33_fetch_pdufa >> /var/log/etl/pdufa.log 2>&1

# News - every 4 hours
0 */4 * * * cd /app && python -m backend.etl.30_fetch_news >> /var/log/etl/news.log 2>&1

# Patents - daily 4am EST
0 9 * * * cd /app && python -m backend.etl.31_fetch_patents >> /var/log/etl/patents.log 2>&1

# Change detection - daily 5am EST
0 10 * * * cd /app && python -m backend.etl.34_detect_changes >> /var/log/etl/changes.log 2>&1

# Weekly digest - Monday 9am EST
0 14 * * 1 cd /app && python -m backend.etl.35_generate_digest >> /var/log/etl/digest.log 2>&1

# Perplexity validation - Sunday midnight
0 5 * * 0 cd /app && python -m backend.etl.36_validate_with_perplexity >> /var/log/etl/validation.log 2>&1
```

---

## Quality Assurance

### Data Accuracy Monitoring

```sql
-- Daily QA query: Check for stale data
SELECT
    entity_type,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE last_api_update > NOW() - INTERVAL '7 days') as fresh,
    COUNT(*) FILTER (WHERE last_api_update <= NOW() - INTERVAL '7 days') as stale
FROM (
    SELECT 'trial' as entity_type, last_api_update FROM ci_trial_calendar
    UNION ALL
    SELECT 'pdufa', updated_at FROM ci_pdufa_dates
    UNION ALL
    SELECT 'drug', last_ot_refresh FROM epi_drugs
) combined
GROUP BY entity_type;
```

### LLM Extraction Accuracy

| Metric | Target | Measurement |
|--------|--------|-------------|
| PDUFA date extraction | >95% accuracy | Manual spot-check 20 records/week |
| News relevance | >90% precision | Track rejected articles |
| Entity linking | >85% accuracy | Perplexity validation |
| Change classification | >90% accuracy | User feedback loop |

### Perplexity Validation Pipeline

```python
# 36_validate_with_perplexity.py
"""
Weekly validation job:
1. Sample 20 drugs with recent changes
2. Query Perplexity for ground truth (phase, approval status, PDUFA)
3. Compare with our database
4. Log discrepancies to fact_check_log
5. Flag critical mismatches for manual review
"""
```

---

## Implementation Timeline

### Week 1: Trial Calendar Foundation ✅ COMPLETED 2025-12-02
- [x] Create `ci_trial_calendar` and `ci_conferences` tables
- [x] Build `32_fetch_trial_dates.py` ETL with tiered query strategy
- [x] Create `ci_curated_trials` table for Tier 1 drugs
- [x] Add `ctgov_query_tier` column to `epi_drugs`
- [x] Seed 2025 oncology conferences (ASCO, ASH, AACR, ESMO, etc.)
- [x] Run full Tier 2 ETL: 991 trials ingested
- [x] Create API endpoints `/calendar/*` (Option C) ✅
- [x] Build Trial Calendar UI page (Option B) ✅

### Week 2: Change Detection + Digest ✅ COMPLETED 2025-12-03
- [x] Create `ci_change_log` and `ci_user_digest_prefs` tables
- [x] Build `34_detect_changes.py` ETL
- [x] Build `35_generate_digest.py` with email template
- [x] Set up Resend email integration
- [x] Test weekly digest flow (preview mode)

### Week 3: PDUFA Tracker
- [ ] Create `ci_pdufa_dates` table
- [ ] Build `33_fetch_pdufa.py` with LLM extraction
- [ ] Build PDUFA calendar UI
- [ ] Integrate Perplexity validation

### Week 4: Watchlist + Alerts
- [ ] Create `ci_watchlist` and `ci_alerts` tables
- [ ] Build Supabase Edge Function for real-time alerts
- [ ] Create watchlist management UI
- [ ] Set up Slack webhook integration

### Week 5: Exports
- [ ] Build PowerPoint export with templates
- [ ] Build Excel export for matrices
- [ ] Build PDF report generation
- [ ] Add export buttons to all relevant views

### Week 6: Polish + Monetization
- [ ] Add Supabase Auth
- [ ] Add Stripe subscription
- [ ] Gated features for paid tier
- [ ] Documentation and onboarding flow
- [ ] Deploy to production

---

## Cost Estimates

### APIs

| Service | Usage | Cost/Month |
|---------|-------|------------|
| ClinicalTrials.gov | Unlimited | Free |
| FDA RSS | Unlimited | Free |
| Perplexity API | ~1000 queries/month | ~$20 |
| Gemini API | ~5000 requests/month | ~$10 |
| Resend Email | ~500 emails/month | Free tier |

### Infrastructure

| Service | Tier | Cost/Month |
|---------|------|------------|
| Supabase | Pro | $25 |
| Render (Backend) | Starter | $7 |
| Vercel (Frontend) | Pro | $20 |
| **Total** | | **~$82/month** |

---

## Success Metrics

| Metric | Target (Month 1) | Target (Month 6) |
|--------|------------------|------------------|
| Trial calendar entries | 500+ | 2000+ |
| PDUFA dates tracked | 50+ | 200+ |
| Weekly digest open rate | 40% | 50% |
| Alert click-through rate | 20% | 30% |
| Paying customers | 3 | 20 |
| MRR | $1,500 | $15,000 |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| CT.gov API rate limits | Batch requests, cache aggressively, 3-sec delays |
| LLM hallucinations | Confidence scoring, Perplexity validation, manual review queue |
| Email deliverability | Use Resend (good reputation), SPF/DKIM setup |
| Data staleness | Daily freshness checks, automated alerts on stale data |
| Scope creep | Strict 6-week timeline, defer "nice-to-haves" |
