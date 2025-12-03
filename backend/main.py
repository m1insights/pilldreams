from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

# API Documentation metadata
API_DESCRIPTION = """
# Phase4 Epigenetics Oncology Intelligence API

**The definitive intelligence platform for epigenetic oncology drug development.**

## Core Capabilities

### 🎯 Epigenetic Targets
- 79 validated epigenetic targets (HDACs, BETs, DNMTs, EZH2, etc.)
- IO exhaustion annotations for combination therapy planning
- Tractability scores from Open Targets

### 💊 Drug Pipeline
- 66 drugs in development (14 FDA-approved)
- Weighted scoring: Bio (50%) + Chem (30%) + Tract (20%)
- Phase tracking, mechanism of action, ChEMBL integration

### 🧬 Epigenetic Editing
- 17 editing programs (CRISPR, TALE-based)
- Delivery/effector scoring
- Target gene validation

### 📊 Competitive Intelligence
- Trial calendar with PDUFA dates
- Change detection and weekly digests
- Company portfolio tracking
- PowerPoint export for landscape decks

## Authentication

Most endpoints require Bearer token authentication:
```
Authorization: Bearer <supabase_access_token>
```

## Rate Limits

| Tier | Requests/min | Exports/month |
|------|--------------|---------------|
| Free | 60 | 5 |
| Pro | 300 | 50 |
| Team | 1000 | Unlimited |
| Enterprise | Unlimited | Unlimited |

## Support

- Documentation: https://phase4.ai/docs
- API Status: https://status.phase4.ai
- Contact: api@phase4.ai
"""

TAGS_METADATA = [
    {
        "name": "Epigenetics",
        "description": "Core epigenetics data: targets, drugs, indications, scores, and signatures.",
    },
    {
        "name": "AI",
        "description": "AI-powered chat and analysis endpoints using Google Gemini.",
    },
    {
        "name": "Calendar",
        "description": "Trial calendar, PDUFA dates, and catalyst tracking.",
    },
    {
        "name": "Watchlist",
        "description": "User watchlist management for tracking entities.",
    },
    {
        "name": "Auth",
        "description": "Authentication endpoints (Supabase-based).",
    },
    {
        "name": "Payments",
        "description": "Subscription management via Stripe.",
    },
    {
        "name": "exports",
        "description": "Export data to Excel, CSV, and PowerPoint formats.",
    },
    {
        "name": "Timeline",
        "description": "Historical tracking of drug phases, company entries, and target activity.",
    },
]

app = FastAPI(
    title="Phase4 Epigenetics Intelligence API",
    description=API_DESCRIPTION,
    version="2.0.0",
    openapi_tags=TAGS_METADATA,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "Phase4 API Support",
        "url": "https://phase4.ai/support",
        "email": "api@phase4.ai",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://phase4.ai/terms",
    },
)

# CORS Configuration
origins = [
    "http://localhost:3000",  # Next.js frontend
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3003",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Epigenetics Intelligence Layer is running"}

from backend.api import endpoints
from backend.api import ai_endpoints
from backend.api import calendar_endpoints
from backend.api import watchlist_endpoints
from backend.api import auth_endpoints
from backend.api import payments_endpoints
from backend.api import exports_endpoints
from backend.api import timeline_endpoints

app.include_router(endpoints.router)
app.include_router(ai_endpoints.router)
app.include_router(calendar_endpoints.router)
app.include_router(watchlist_endpoints.router)
app.include_router(auth_endpoints.router)
app.include_router(payments_endpoints.router)
app.include_router(exports_endpoints.router)
app.include_router(timeline_endpoints.router)

