# 💊 pilldreams

**Drug Intelligence Platform** for retail biotech investors, researchers, and clinicians.

## Overview

pilldreams provides comprehensive drug analysis:

- **Approval Probability** - ML predictions for pipeline drugs
- **Mechanism of Action** - Targets, receptors, chemical structure
- **Trial Progress** - Phase data, timelines, endpoints
- **Safety Signals** - FDA adverse events analysis
- **Evidence Strength** - RCTs, meta-analyses, publications
- **Real-World Sentiment** - Patient and practitioner perspectives
- **AI Chat Assistant** - Context-aware drug intelligence

## Architecture

Built with **MCP-based agent architecture** following [Anthropic's code execution pattern](https://www.anthropic.com/engineering/code-execution-with-mcp):

- **98.7% token savings** via progressive disclosure
- **5 specialized agents**: Orchestrator, Playwright, Supabase, Context7, Streamlit
- **Skills library**: Reusable code patterns
- **Context caching**: Avoid redundant tool discovery

## Tech Stack

- **Frontend**: Streamlit
- **Database**: Supabase (PostgreSQL)
- **Agents**: Python async + MCP protocol
- **Data Sources**: ClinicalTrials.gov, DrugBank, ChEMBL, OpenFDA, PubMed, Reddit
- **AI**: Claude API with context injection

## Quick Start

### 1. Prerequisites

- Python 3.9+
- Supabase account (free tier works)
- Anthropic API key

### 2. Installation

```bash
# Clone repository
cd /Users/mananshah/Dev/pilldreams

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required credentials:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anon key
- `ANTHROPIC_API_KEY` - Your Claude API key

### 4. Initialize Database

```bash
# Run Supabase schema (via Supabase dashboard SQL editor)
# Copy contents of core/schema.sql and execute in Supabase

# Or use the client script (once Supabase is configured)
python core/supabase_client.py --init --seed
```

### 5. Run Application

```bash
streamlit run app/main.py
```

Visit `http://localhost:8501` in your browser.

## Project Structure

```
/pilldreams
├── agents/                 # MCP-based specialized agents
│   ├── orchestrator/      # Main coordinator
│   ├── playwright_agent/  # Web scraping
│   ├── supabase_agent/    # Database operations
│   ├── context7_agent/    # Documentation lookup
│   └── streamlit_agent/   # UI/visualization
├── mcp_servers/           # MCP tool wrappers
│   ├── playwright/        # Playwright tools
│   ├── supabase/          # Supabase tools
│   └── context7/          # Context7 tools
├── app/                   # Streamlit UI
│   ├── main.py           # Entry point
│   └── tabs/             # UI tabs
├── core/                  # Core functionality
│   ├── scoring.py        # Scoring algorithms
│   ├── supabase_client.py # Database client
│   └── schema.sql        # Database schema
├── ingestion/            # Data collection scripts
└── workspace/            # Agent execution cache
```

## Development

### Using the `/task2` Command (Recommended)

The **fastest way to build features** in pilldreams:

```
/task2 Add a radar chart to the Overview tab
/task2 Scrape DrugBank for metformin mechanism data
/task2 Create a trial timeline visualization
```

The `/task2` command orchestrates all agents, writes code, tests in Streamlit, and documents everything automatically.

**See:** `.claude/commands/README.md` for full usage guide

**Task Log:** `tasks.md` tracks all completed tasks

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black .

# Type checking
mypy agents/ core/

# Linting
flake8
```

## Agent Architecture

### Progressive Disclosure

Agents load tools on-demand instead of upfront:

**Before:** 150,000 tokens (all tool definitions)
**After:** 2,000 tokens (load as needed)
**Savings:** 98.7%

### Skills Library

Agents build reusable code over time:

```python
# agents/playwright_agent/skills/scrape-drugbank.py
# Saved skill that can be reused across sessions
```

### Context Caching

Tool definitions cached to avoid re-discovery:

```json
// agents/{agent}/context/tools.json
{
  "last_updated": "2025-11-21T...",
  "tools": [...]
}
```

## Data Sources

### Direct APIs
- **ClinicalTrials.gov** - Trial data
- **ChEMBL API** - Binding affinity
- **PubMed E-utilities** - Evidence classification
- **OpenFDA** - Adverse events

### Web Scraping
- **DrugBank** - Mechanism of action
- **Reddit** - Real-world sentiment

## Roadmap

### Phase 0 - Setup ✅
- [x] Project structure
- [x] Agent scaffolds
- [x] Streamlit skeleton
- [x] Supabase schema

### Phase 1 - Hardcoded Prototype
- [ ] Load 1-2 sample drugs
- [ ] Build UI with placeholder data
- [ ] Establish design patterns

### Phase 2 - Core Ingestion
- [ ] ClinicalTrials.gov integration
- [ ] DrugBank scraping
- [ ] ChEMBL API
- [ ] Trial Progress Score
- [ ] Mechanism Score

### Phase 3 - Safety & Evidence
- [ ] OpenFDA integration
- [ ] PubMed integration
- [ ] Safety Score
- [ ] Evidence Score

### Phase 4 - Sentiment & AI
- [ ] Reddit sentiment analysis
- [ ] AI chat with context injection

### Phase 5 - Polish
- [ ] Layout improvements
- [ ] More drugs
- [ ] About/Methodology page
- [ ] Export functionality

## Contributing

This is currently a personal project. If you'd like to contribute, please reach out.

## License

Proprietary - All rights reserved

## Disclaimer

**For informational purposes only.** This app should not be used as medical advice or investment guidance. Always consult qualified professionals.

## Contact

**Developer**: Manan Shah
**Start Date**: November 2025
**Current Phase**: Phase 0 (Setup Complete)

---

Built with ❤️ using Claude Code and MCP
