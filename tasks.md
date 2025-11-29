# Phase4 Analytics - Task Log

## [2025-11-28 Session] Task: Customer Persona UI Evaluation

**Status:** ✅ Completed

**Description:**
Evaluate the Phase4 Epigenetics Oncology Intelligence platform UI from the perspective of three customer personas: Scientist, Business Development, and Portfolio Manager.

**Agents Used:**
- Playwright MCP: Browser automation to navigate and capture UI state
- Persona Evaluation: Manual assessment from each customer perspective

**Current UI State:**
- Homepage: Landing page with hero, pricing, FAQ sections
- Targets Page: `/explore/targets` - Shows 67 targets with family filters
- Target Detail: `/target/{uuid}` - **BROKEN** (422 error)
- Drugs Page: Not accessible from navigation

---

## Persona Evaluations

### 🔬 Scientist Agent (Dr. Elena - Oncology Researcher)

**Goal:** Validate epigenetic targets for grant proposals and research direction

| Feature | Status | Notes |
|---------|--------|-------|
| Target Browsing | ✅ Good | 67 targets visible with family/class categorization |
| Filter by Family | ✅ Good | HDAC, BET, DNMT, HMT, KDM, IDH, TET, SIRT buttons |
| BioScore Visibility | ⚠️ Partial | Scores show but missing underlying evidence breakdown |
| Target Detail Page | ❌ Broken | 422 error when clicking target - UUID not handled |
| External Links | ❌ Missing | No links to UniProt, Open Targets, or PubMed |
| Mechanism Info | ⚠️ Minimal | "writer/eraser/reader" shown but no detailed MOA |

**Critical Issues:**
1. **BLOCKING**: Target detail page broken (422 error)
2. **HIGH**: No disease association data visible
3. **MEDIUM**: Missing external database links
4. **LOW**: Would like literature citations

---

### 💼 Business Development Agent (James - BD Manager)

**Goal:** Identify in-licensing opportunities and competitive landscape

| Feature | Status | Notes |
|---------|--------|-------|
| Drug List View | ⚠️ Not Found | No dedicated drugs page in navigation |
| Total Score Ranking | ⚠️ Unknown | Scores in targets table, no drug ranking |
| Company Info | ❌ Missing | No sponsor/developer info visible |
| Pipeline Stage | ❌ Missing | No Phase 1/2/3 information displayed |
| Competitive Landscape | ❌ Missing | Cannot see who else targets same protein |
| Deal History | ❌ Missing | No licensing/partnership data |

**Critical Issues:**
1. **BLOCKING**: No Drugs page - nav link goes to `/#search`
2. **HIGH**: Need Company-to-Asset mapping
3. **HIGH**: No pipeline stage filtering
4. **MEDIUM**: No export functionality

---

### 📊 Portfolio Manager Agent (David - Healthcare PM)

**Goal:** Due diligence on epigenetics biotech investments

| Feature | Status | Notes |
|---------|--------|-------|
| Score Dashboard | ⚠️ Partial | Avg BioScore shown, no breakdown |
| Asset Count | ✅ Good | 83 pipeline assets, 67 targets visible |
| Risk Assessment | ❌ Missing | No tractability concerns or dev risk |
| Market Sizing | ❌ Missing | No indication market size |
| Competitive Positioning | ❌ Missing | Cannot compare assets head-to-head |
| Data Export | ❌ Missing | No CSV/Excel export |
| Watchlist | ❌ Missing | Cannot save/track assets |

**Critical Issues:**
1. **BLOCKING**: Cannot access drug detail pages
2. **HIGH**: Need score breakdown visualization (radar chart)
3. **HIGH**: No sorting by TotalScore
4. **MEDIUM**: No comparative views

---

## Prioritized Improvements

### 🚨 P0 - BLOCKING BUGS (Must Fix Now)

| Issue | Impact | Root Cause |
|-------|--------|------------|
| Target/Drug detail pages return 422 | All personas blocked | Backend expects `int` ID but receives UUID string |
| Drugs nav link broken | BD/PM blocked | Link goes to `/#search` not `/explore/drugs` |
| Homepage search shows "No targets found" | Confusing UX | API timing or hydration issue |

### 🔴 P1 - HIGH PRIORITY (Next Sprint)

| Feature | Persona | Effort |
|---------|---------|--------|
| Create Drugs List Page | BD, PM | Medium |
| Sort targets/drugs by TotalScore | PM | Low |
| Pipeline Phase filtering | BD | Medium |
| Company-to-Asset mapping | BD | High |
| Score breakdown visualization | PM, Scientist | Medium |

### 🟡 P2 - MEDIUM PRIORITY

| Feature | Persona | Effort |
|---------|---------|--------|
| External database links | Scientist | Low |
| Disease association display | Scientist | Medium |
| Data export (CSV) | PM, BD | Low |
| Comparative views | PM | High |

### 🟢 P3 - LOW PRIORITY (Backlog)

| Feature | Persona |
|---------|---------|
| Watchlist/alerts | PM |
| Deal history | BD |
| Literature citations | Scientist |
| Company financials | PM |

---

## Technical Notes

**Bug: 422 Error on Detail Pages**

Location: `backend/api/endpoints.py:143-144`
```python
@router.get("/targets/{target_id}")
async def get_target(target_id: int):  # <-- Expects int, receives UUID string
```

**Fix Required:** Change parameter type from `int` to `str` for all detail endpoints:
- `/targets/{target_id}`
- `/drugs/{drug_id}`
- `/indications/{indication_id}`

---

## Screenshots

- `/.playwright-mcp/phase4-targets-page.png` - Full targets table view

---

## Next Actions

1. **Immediate**: Fix UUID handling in backend API endpoints
2. **This Week**: Create `/explore/drugs` page with sorting
3. **Next Sprint**: Add company mapping and score visualizations
