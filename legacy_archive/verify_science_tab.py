
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from core.supabase_client import get_client

def test_science_render():
    db = get_client()
    
    # 1. Get a company with data
    print("Fetching company...")
    # Try ROIV or a company we know has data
    company = db.client.table("company").select("*").eq("ticker", "IBRX").single().execute().data
    
    if not company:
        print("Company IBRX not found")
        return

    print(f"Testing render for {company['ticker']}...")
    company_id = company['id']
    
    # 2. Fetch Drugs
    drugs = db.client.table("company_drug").select("drug(id, name)").eq("company_id", company_id).execute().data
    print(f"Found {len(drugs)} drugs")
    
    if not drugs:
        return
        
    drug_list = [d['drug'] for d in drugs if d['drug']]
    
    for drug in drug_list:
        print(f"  Drug: {drug['name']}")
        
        # 3. Fetch Targets
        targets_response = db.client.table("drugtarget").select("target(id, name, uniprot_id)").eq("drug_id", drug['id']).execute()
        targets = [t['target'] for t in targets_response.data if t['target']]
        print(f"    Found {len(targets)} targets")
        
        for target in targets:
            print(f"    Target: {target['name']} ({target['uniprot_id']})")
            
            # 4. Fetch Associations
            associations = db.client.table("target_disease_association").select("*").eq("target_id", target['id']).limit(5).execute().data
            print(f"      Found {len(associations)} associations")
            for a in associations:
                print(f"        - {a['disease_name']}: {a['association_score']}")

if __name__ == "__main__":
    test_science_render()
