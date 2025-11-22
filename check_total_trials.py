import requests
import sys

# Build query for active Phase 1-3 trials
phases = ["PHASE1", "PHASE2", "PHASE3"]
statuses = ["RECRUITING", "ACTIVE_NOT_RECRUITING", "ENROLLING_BY_INVITATION", "NOT_YET_RECRUITING"]

# Build query string
query_parts = []

# Phase filter
phase_query = " OR ".join([f"AREA[Phase]{p}" for p in phases])
query_parts.append(f"({phase_query})")

# Status filter
status_query = " OR ".join([f'AREA[OverallStatus]"{s}"' for s in statuses])
query_parts.append(f"({status_query})")

params = {
    "format": "json",
    "pageSize": 1,  # Just need total count
    "query.cond": " AND ".join(query_parts)
}

print("🔍 Querying ClinicalTrials.gov for total active Phase 1-3 trials...")
print(f"   Phases: {phases}")
print(f"   Statuses: {statuses}\n")

try:
    response = requests.get(
        "https://clinicaltrials.gov/api/v2/studies",
        params=params,
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        total = data.get("totalCount", 0)
        
        print(f"✅ Total trials matching criteria: {total:,}")
        print(f"\n📊 Current ingestion status:")
        print(f"   • Ingested so far: 500 trials")
        print(f"   • Remaining: {total - 500:,} trials")
        print(f"   • Completion: {500/total*100:.1f}%")
        
        # Estimate time
        trials_per_minute = 50  # Conservative estimate based on rate limiting
        remaining_minutes = (total - 500) / trials_per_minute
        print(f"\n⏱️  Estimated time for full ingestion: ~{remaining_minutes:.0f} minutes ({remaining_minutes/60:.1f} hours)")
    else:
        print(f"❌ API error: {response.status_code}")
        print(response.text[:500])
        
except Exception as e:
    print(f"❌ Error: {e}")
