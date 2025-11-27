
import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from core.supabase_client import get_client

def check_quality():
    db = get_client()
    print("--- DATA QUALITY REPORT ---\n")
    
    # 1. Drug Name Cleanliness
    print("1. Drug Name Hygiene:")
    junk_terms = ["Tablet", "Placebo", "Capsule", "Injection", "mg", "Standard of Care"]
    drugs = db.client.table("drug").select("name").execute().data
    
    junk_found = []
    for d in drugs:
        for term in junk_terms:
            if term.lower() in d['name'].lower():
                junk_found.append(d['name'])
                
    if junk_found:
        print(f"⚠️ Found {len(junk_found)} potential junk entries: {junk_found[:5]}...")
    else:
        print("✅ No obvious junk terms found in drug names.")
        
    # 2. Financial Data Sanity
    print("\n2. Financial Data Sanity:")
    companies = db.client.table("company").select("ticker, cash_balance, monthly_burn_rate").not_.is_("cash_balance", "null").execute().data
    
    negative_cash = [c['ticker'] for c in companies if c['cash_balance'] < 0]
    if negative_cash:
        print(f"⚠️ Found companies with negative cash: {negative_cash}")
    else:
        print(f"✅ All {len(companies)} companies have positive cash balances.")
        
    # 3. Science Data Linkage
    print("\n3. Science Data Coverage:")
    targets = db.client.table("target").select("count", count="exact").execute().count
    associations = db.client.table("target_disease_association").select("count", count="exact").execute().count
    
    print(f"✅ Targets Enriched: {targets}")
    print(f"✅ Disease Associations: {associations}")
    
    if associations == 0:
        print("⚠️ No disease associations found (did the ingestion finish?)")

if __name__ == "__main__":
    check_quality()
