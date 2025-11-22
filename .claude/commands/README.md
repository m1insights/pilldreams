# pilldreams Custom Commands

## `/task2` - Task Orchestrator

**The main command for building pilldreams features.**

### Usage

```
/task2 Add a radar chart to the Overview tab
```

```
/task2 Scrape DrugBank for metformin mechanism data
```

```
/task2 Create a trial timeline visualization with Plotly
```

### What It Does

The `/task2` command is an intelligent orchestrator that:

1. **Analyzes** your task to determine which agents are needed
2. **Routes** to specialized agents (Playwright, Supabase, Context7, Streamlit)
3. **Executes** the work using MCP code execution pattern
4. **Tests** by running Streamlit and debugging issues
5. **Documents** the completed task in `tasks.md`

### Example Workflow

**You type:**
```
/task2 Add drug scores radar chart to Overview tab
```

**Claude will:**
1. ✅ Classify task → UI Development
2. ✅ Route to Context7 Agent → Get Plotly radar chart examples
3. ✅ Route to Streamlit Agent → Implement chart in `app/tabs/overview.py`
4. ✅ Save skill → `agents/streamlit_agent/skills/radar-chart.py`
5. ✅ Test → Run `streamlit run app/main.py`
6. ✅ Debug → Fix any errors until app runs
7. ✅ Document → Append to `tasks.md` with timestamp

### Task Types

**Data Ingestion:**
- `/task2 Scrape DrugBank for metformin data`
- `/task2 Fetch trial data from ClinicalTrials.gov for aspirin`
- Agents used: Playwright → Supabase

**UI Development:**
- `/task2 Add a timeline chart for clinical trials`
- `/task2 Create metric cards for drug scores`
- Agents used: Context7 → Streamlit

**Database Operations:**
- `/task2 Create query to get all Phase III trials`
- `/task2 Add indexes to Trial table for performance`
- Agents used: Supabase

**Full Features:**
- `/task2 Build complete Pharmacology tab with RDKit structures`
- Agents used: Context7 → Playwright → Supabase → Streamlit

### Key Features

✅ **Autonomous Execution** - Agents work independently
✅ **Progressive Disclosure** - Load tools on-demand (98.7% token savings)
✅ **Skills Library** - Reusable code patterns saved automatically
✅ **Automatic Testing** - Streamlit app runs before task is "complete"
✅ **Comprehensive Logging** - Every task documented in `tasks.md`

### Task Log

All completed tasks are logged in:
**File:** `/Users/mananshah/Dev/pilldreams/tasks.md`

Each entry includes:
- Date/time
- Description
- Agents used
- Files modified
- Testing results
- Notes

### Tips for Best Results

1. **Be specific:** "Add radar chart to Overview tab" > "improve overview"
2. **One feature at a time:** Break large tasks into smaller pieces
3. **Trust the agents:** They'll find the right docs and write working code
4. **Review tasks.md:** Check what was done and how

### Advanced Usage

**Chain multiple tasks:**
```
/task2 Scrape DrugBank mechanism for metformin
/task2 Store mechanism data in Supabase
/task2 Display mechanism in Pharmacology tab
```

**Debugging tasks:**
```
/task2 Fix the radar chart in Overview tab (it's not displaying)
```

**Optimization tasks:**
```
/task2 Optimize the trial query to use database indexes
```

---

**Ready to build? Try `/task2` with your first feature!**
