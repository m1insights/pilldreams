
import random
import sys
from pathlib import Path
import structlog
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.supabase_client import get_client

load_dotenv()
logger = structlog.get_logger()

def run_spot_check():
    db = get_client()
    
    print("Fetching company list...")
    # Fetch all IDs to sample randomly
    all_companies = db.client.table("company").select("id, name, ticker").execute().data
    
    if not all_companies:
        print("No companies found!")
        return

    sample_size = min(25, len(all_companies))
    sampled_companies = random.sample(all_companies, sample_size)
    
    print(f"\nPerforming Spot Check on {sample_size} Companies...\n")
    
    for company in sampled_companies:
        c_id = company['id']
        c_name = company['name']
        ticker = company['ticker']
        
        print(f"=== {c_name} ({ticker}) ===")
        
        # 1. Get Trials
        # We look for trials where this company is the sponsor
        trial_count = db.client.table("trial").select("count", count="exact").eq("sponsor_company_id", c_id).execute().count
        print(f"  Trials: {trial_count}")
        
        # 2. Get Drugs
        cd_links = db.client.table("company_drug").select("drug_id, development_stage").eq("company_id", c_id).execute().data
        
        if not cd_links:
            print("  Drugs: 0 (No linked drugs)")
            print("-" * 40)
            continue
            
        print(f"  Drugs: {len(cd_links)}")
        
        drug_ids = [x['drug_id'] for x in cd_links]
        # Fetch drug details
        drugs = db.client.table("drug").select("id, name, chembl_id").in_("id", drug_ids).execute().data
        
        # Map back stage
        drug_stage_map = {x['drug_id']: x['development_stage'] for x in cd_links}
        
        for drug in drugs:
            d_id = drug['id']
            name = drug['name']
            chembl_id = drug['chembl_id']
            stage = drug_stage_map.get(d_id, "Unknown")
            
            # Count targets
            target_count = db.client.table("drugtarget").select("count", count="exact").eq("drug_id", d_id).execute().count
            
            chembl_status = f"✅ ({chembl_id})" if chembl_id else "❌"
            target_status = f"{target_count} targets" if target_count > 0 else "No binding data"
            
            print(f"    • {name} [{stage}]")
            print(f"      ChEMBL: {chembl_status} | Science: {target_status}")
            
        print("-" * 40)

if __name__ == "__main__":
    run_spot_check()
