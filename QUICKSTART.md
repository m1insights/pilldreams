# 🚀 pilldreams Quick Start

## The Fastest Way to Build: `/task2` Command

```bash
/task2 {your task here}
```

### Examples

```bash
# UI Development
/task2 Add a radar chart showing drug scores to the Overview tab
/task2 Create a trial timeline visualization with Plotly
/task2 Add metric cards for safety scores

# Data Ingestion
/task2 Scrape DrugBank for metformin mechanism data
/task2 Fetch trials from ClinicalTrials.gov for aspirin
/task2 Get adverse events from OpenFDA for sertraline

# Database Operations
/task2 Create a query to get all active Phase III trials
/task2 Add composite index on Trial table for drug_id + phase
/task2 Seed database with 10 sample drugs

# Full Features
/task2 Build the complete Pharmacology tab with RDKit molecule viewer
/task2 Implement the AI chat with context injection
/task2 Add Reddit sentiment scraping and visualization
```

## What `/task2` Does Automatically

1. ✅ **Analyzes** your task
2. ✅ **Routes** to the right agents (Playwright, Supabase, Context7, Streamlit)
3. ✅ **Writes** actual working code
4. ✅ **Tests** by running Streamlit
5. ✅ **Debugs** any errors
6. ✅ **Documents** in `tasks.md`

## Your Agent Team

| Agent | Specialty | MCP Tools |
|-------|-----------|-----------|
| **Orchestrator** | Routes tasks | None (delegates) |
| **Playwright** | Web scraping | Browser automation |
| **Supabase** | Database ops | Queries, inserts |
| **Context7** | Docs lookup | Library examples |
| **Streamlit** | UI/viz | Charts, layouts |

## Token Efficiency

**Traditional Approach:**
- Load all tool definitions: ~150,000 tokens
- Pass all data through context: +50,000 tokens

**Our MCP Pattern:**
- Load tools on-demand: ~2,000 tokens
- Filter in execution environment: ~500 tokens
- **Savings: 98.7%** 🚀

## Project Status

**Phase:** 0 → 1 (Setup Complete, Starting Prototype)

**Ready to Use:**
- ✅ 5 specialized agents
- ✅ MCP tool wrappers (Playwright, Supabase, Context7)
- ✅ Streamlit UI skeleton (5 tabs)
- ✅ Supabase schema (8 tables)
- ✅ `/task2` orchestrator command

**Verified Working:**
- ✅ Context7 MCP (fetched Streamlit docs)
- ⏳ Playwright MCP (not yet tested)
- ⏳ Supabase MCP (pending setup)

## First Steps

### 1. Install Dependencies

```bash
cd /Users/mananshah/Dev/pilldreams
python3 -m venv venv
source venv/bin/activate
pip install streamlit plotly pandas
```

### 2. Run Streamlit (Placeholder Data)

```bash
streamlit run app/main.py
```

Visit: http://localhost:8501

### 3. Set Up Supabase (Optional)

```bash
# Copy environment template
cp .env.example .env

# Add your credentials
nano .env

# Run schema in Supabase SQL Editor
# (Copy core/schema.sql)
```

### 4. Start Building!

```bash
/task2 Add working radar chart to Overview tab
```

## Task Log

**All tasks are documented in:** `tasks.md`

Each entry shows:
- Date/time
- What was built
- Which agents were used
- What files changed
- Testing results

## Key Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Full project context (1,264 lines) |
| `tasks.md` | Completed task log |
| `README.md` | Project documentation |
| `.claude/commands/task2.md` | Orchestrator command |
| `requirements.txt` | Python dependencies |
| `core/schema.sql` | Supabase schema |

## Getting Help

**Command Help:**
```bash
cat .claude/commands/README.md
```

**Project Context:**
```bash
cat CLAUDE.md | grep "##"  # Section headers
```

**Task History:**
```bash
cat tasks.md
```

---

**Ready to build pilldreams? Start with `/task2`!** 💊
