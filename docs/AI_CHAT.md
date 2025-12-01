# AI Chat Layer Documentation

**Last Updated:** 2025-11-29

## Overview

The pilldreams AI chat layer provides an intelligent interface for exploring epigenetic oncology data. It uses Google Gemini to generate grounded responses based on database content.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   FastAPI        │────▶│   Gemini API    │
│   (Next.js)     │     │   /ai/*          │     │   (LLM)         │
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
                        ┌────────▼─────────┐
                        │  Context Builder │
                        │  (DB Queries)    │
                        └────────┬─────────┘
                                 │
                        ┌────────▼─────────┐
                        │    Supabase      │
                        │    (PostgreSQL)  │
                        └──────────────────┘
```

## Key Components

### 1. AI Client (`backend/ai/client.py`)

Model-agnostic abstraction for LLM interactions.

```python
from backend.ai.client import get_ai_client

client = get_ai_client()  # Returns GeminiClient or MockAIClient

response = client.generate(
    prompt="What is Vorinostat?",
    system_prompt=SYSTEM_PROMPTS["chat"],
    context={"drugs": [...], "targets": [...]}
)
```

**Supported Clients:**
- `GeminiClient`: Production client using Google Gemini 2.0 Flash
- `MockAIClient`: Testing client that returns mock responses

### 2. Context Builder (`backend/ai/context_builder.py`)

Retrieves and structures database data for AI context.

```python
from backend.ai.context_builder import ContextBuilder

cb = ContextBuilder()

# Extract entities from question
entities = cb.extract_entities_from_question("Compare HDAC inhibitors to BET inhibitors")
# Returns: {"drug_names": [], "target_symbols": ["HDAC1", "HDAC2", ..., "BRD4"], ...}

# Get full drug context
drug_ctx = cb.get_drug_context("VORINOSTAT")
# Returns: {"drug": {...}, "targets": [...], "indications": [...], "chembl_metrics": {...}}

# Get scorecard context
scorecard = cb.get_scorecard_context(drug_id, indication_id)
# Returns: Full context with scores, targets, formula explanation
```

### 3. System Prompts (`backend/ai/prompts.py`)

Pre-defined prompts for different use cases:

| Prompt | Purpose |
|--------|---------|
| `chat` | General Q&A about epigenetics drugs |
| `scorecard` | Explain drug-indication scorecards |
| `editing_asset` | Explain epigenetic editing programs |
| `query` | Answer database queries |

## API Endpoints

### POST `/ai/chat`

General chat endpoint for epigenetics questions.

**Request:**
```json
{
  "question": "What is Vorinostat used for?",
  "entity_refs": {
    "drug_names": ["VORINOSTAT"],
    "target_symbols": [],
    "indication_names": []
  },
  "conversation_history": [],
  "temperature": 0.7
}
```

**Response:**
```json
{
  "answer": "Vorinostat (Zolinza) is an FDA-approved HDAC inhibitor...",
  "entities_found": {"drug_names": ["VORINOSTAT"], ...},
  "model_used": "gemini-2.0-flash"
}
```

### POST `/ai/explain-scorecard`

Explain why a drug has its current scores for an indication.

**Request:**
```json
{
  "drug_id": "uuid-here",
  "indication_id": "uuid-here",
  "temperature": 0.5
}
```

**Response:**
```json
{
  "explanation": "Vorinostat scores 46/100 for CTCL...",
  "drug_name": "VORINOSTAT",
  "indication_name": "Cutaneous T-cell lymphoma",
  "scores": {
    "bio_score": 33.2,
    "chem_score": 30.0,
    "tractability_score": 85.0,
    "total_score": 45.6
  },
  "model_used": "gemini-2.0-flash"
}
```

### POST `/ai/explain-editing-asset`

Explain an epigenetic editing program.

**Request:**
```json
{
  "asset_id": "uuid-here",
  "temperature": 0.5
}
```

**Response:**
```json
{
  "explanation": "TUNE-401 uses LNP-delivered dCas9 with DNMT3A/3L...",
  "asset_name": "TUNE-401",
  "target_symbol": "PCSK9",
  "scores": {...},
  "model_used": "gemini-2.0-flash"
}
```

### GET `/ai/entities`

List all known entities for autocomplete.

### GET `/ai/health`

Check if AI service is configured.

## Example Questions

The AI can answer:

1. **Drug explanations:**
   - "What is Vorinostat used for?"
   - "Explain Tazemetostat's mechanism of action"

2. **Score explanations:**
   - "Why does Vorinostat score 46 in CTCL?"
   - "Explain the ChemScore for Belinostat"

3. **Comparisons:**
   - "Compare HDAC inhibitors to BET inhibitors"
   - "How do EZH2 inhibitors differ from DNMT inhibitors?"

4. **Target questions:**
   - "What is EZH2 and why is it a good cancer target?"
   - "Which drugs target HDAC1?"

5. **Database queries:**
   - "List all Phase 3 epigenetic drugs"
   - "Show approved HDAC inhibitors"

6. **Editing assets:**
   - "Describe the PCSK9 epigenetic editors"
   - "How does epigenetic silencing compare to small molecules?"

## Configuration

### Environment Variables

```bash
# Required for production
GEMINI_API_KEY=your-api-key-here

# Supabase (already configured)
SUPABASE_URL=...
SUPABASE_KEY=...
```

### Model Selection

Default: `gemini-2.0-flash` (fast, cost-effective)

To use a different model:
```python
from backend.ai.client import GeminiClient
client = GeminiClient(model_name="gemini-1.5-pro")
```

## Grounding Rules

The AI follows strict grounding rules:

1. **Database facts only:** Drug names, scores, phases, dates must come from provided context
2. **No hallucination:** Never invent drugs, targets, or scores
3. **General knowledge allowed:** May use epigenetics knowledge for mechanism explanations
4. **Clear attribution:** States when data is not in database

## Cost Optimization

- Uses compact JSON context (only relevant entities)
- Caches explanations per drug-indication pair (TODO)
- Uses fast model by default (gemini-2.0-flash)

## Future Enhancements

1. Response caching per entity combination
2. Function calling for dynamic queries
3. Streaming responses
4. Multi-turn conversation memory
5. Model routing (fast vs. reasoning)
