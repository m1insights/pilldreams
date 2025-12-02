#!/usr/bin/env python3
"""Verify trial calendar data after ETL run."""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from supabase import create_client

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_KEY') or os.environ.get('SUPABASE_KEY')
client = create_client(url, key)

# Count by phase
result = client.from_('ci_trial_calendar').select('phase').execute()
phases = {}
for r in result.data:
    p = r['phase'] or 'Unknown'
    phases[p] = phases.get(p, 0) + 1

print('=== TRIAL CALENDAR SUMMARY ===')
print(f'Total trials: {len(result.data)}')
print()
print('By Phase:')
for phase, count in sorted(phases.items(), key=lambda x: -x[1]):
    print(f'  {phase}: {count}')

# Count by status
result2 = client.from_('ci_trial_calendar').select('status').execute()
statuses = {}
for r in result2.data:
    s = r['status'] or 'Unknown'
    statuses[s] = statuses.get(s, 0) + 1

print()
print('By Status:')
for status, count in sorted(statuses.items(), key=lambda x: -x[1]):
    print(f'  {status}: {count}')

# Count by drug
result_drugs = client.from_('ci_trial_calendar').select('drug_name').execute()
drugs = {}
for r in result_drugs.data:
    d = r['drug_name'] or 'Unknown'
    drugs[d] = drugs.get(d, 0) + 1

print()
print('Top 10 Drugs by Trial Count:')
for drug, count in sorted(drugs.items(), key=lambda x: -x[1])[:10]:
    print(f'  {drug}: {count}')

# Upcoming readouts (next 6 months)
six_months = (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d')
today = datetime.now().strftime('%Y-%m-%d')
result3 = client.from_('ci_trial_calendar').select(
    'nct_id,drug_name,phase,primary_completion_date,status'
).lte('primary_completion_date', six_months).gte(
    'primary_completion_date', today
).order('primary_completion_date').limit(15).execute()

print()
print('=== UPCOMING READOUTS (Next 6 Months) ===')
for t in result3.data:
    print(f"  {t['primary_completion_date']} | {t['drug_name']} | {t['phase']} | {t['status']}")

# High-value upcoming trials (Phase 2/3)
result4 = client.from_('ci_trial_calendar').select(
    'nct_id,drug_name,phase,primary_completion_date,status,lead_sponsor'
).lte('primary_completion_date', six_months).gte(
    'primary_completion_date', today
).in_('phase', ['PHASE2', 'PHASE3', 'Phase 2', 'Phase 3']).order(
    'primary_completion_date'
).limit(10).execute()

print()
print('=== HIGH-VALUE READOUTS (Phase 2/3, Next 6 Months) ===')
for t in result4.data:
    print(f"  {t['primary_completion_date']} | {t['drug_name']} | {t['phase']} | {t['lead_sponsor']}")
