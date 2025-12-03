---
description: Fact-check drug, target, or clinical data using Perplexity MCP
---

Use the perplexity-fact-checker agent to verify the data specified by the user.

User query: $ARGUMENTS

## IMPORTANT: Check History First

Before running any fact-check, read `/Users/mananshah/Dev/pilldreams/docs/PERPLEXITY_HISTORY.md` to:
1. Check if this topic was recently verified (avoid duplicate work)
2. Find existing fix scripts that can be reused
3. Reference previous discrepancies and sources

## Workflow

If no specific query is provided, ask the user what they want to fact-check. Examples:
- A specific drug (e.g., "fact-check GSK126 clinical phase and mechanism")
- A target (e.g., "verify EZH2 tractability data")
- Recent ETL data (e.g., "spot-check the latest flagship drugs we ingested")
- Company ownership (e.g., "verify company-drug assignments")

The agent should:
1. **Read history file** - Check `/docs/PERPLEXITY_HISTORY.md` for prior work
2. **Identify what needs to be verified** - Parse user query
3. **Query authoritative sources** - Use WebSearch for FDA, SEC, company PRs
4. **Compare against database** - Query Supabase for current values
5. **Report discrepancies** - With source citations and URLs
6. **Create fix scripts** - If corrections needed, create ETL script in `backend/etl/`
7. **Clean up temp files** - Delete any temporary or one-off scripts that:
   - Were created for debugging but not needed long-term
   - Had errors and were replaced by corrected versions
   - Are not reusable for future fact-checks
   - Example: If you create `temp_check.py` or `debug_query.py`, delete them after use
8. **Update history file** - Append new section to `PERPLEXITY_HISTORY.md` with:
   - Date and task description
   - Sources consulted
   - Discrepancies found (table format)
   - Scripts created (with run commands)
   - Files modified
   - Verification sources (URLs)

## History File Format

Add entries with this structure:
```markdown
## YYYY-MM-DD: [Task Title]

### Task Description
[What was verified]

### Query
[Original user query]

### Sources Used
[List of authoritative sources]

### Discrepancies Found
[Table of issues]

### Scripts Created
[Script paths and run commands]

### Files Modified
[List of modified files]

### Verification Sources
[URLs with citations]

### Files Deleted (Cleanup)
[List any temp files removed, e.g., "Deleted temp_debug.py - one-time debugging script"]
```

This ensures future fact-checks can reference prior work and reuse scripts.

## Cleanup Guidelines

**Keep these files** (reusable):
- ETL scripts with numbered prefixes (e.g., `40_fix_company_drug_ownership.py`)
- Seed CSV files with corrected data
- Documentation updates

**Delete these files** (not reusable):
- `temp_*.py` - Temporary scripts
- `debug_*.py` - Debugging scripts
- `test_*.py` in etl folder - One-off test scripts (not in tests/ folder)
- Any script that was corrected/replaced by a better version
- Inline Python scripts that were run via `python3 << 'EOF'`

After cleanup, note deleted files in the history entry under "Files Deleted (Cleanup)".
