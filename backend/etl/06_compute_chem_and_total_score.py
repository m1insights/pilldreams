import sys
import os
from backend.etl import supabase_client

# Ensure we can import backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

def run():
    print("⚗️ Computing ChemScore & TotalScore...")
    
    if not supabase_client.supabase:
        print("❌ Supabase client not initialized.")
        return

    # 1. Fetch all scores (Bio & Tractability computed)
    scores = supabase_client.supabase.table("epi_scores").select("*").execute().data
    print(f"Found {len(scores)} score records.")
    
    for record in scores:
        drug_id = record["drug_id"]
        
        # Fetch ChemMetrics for Drug
        # We need to join or fetch separately.
        metrics = supabase_client.supabase.table("chembl_metrics").select("chem_score").eq("drug_id", drug_id).execute().data
        
        chem_score = 0
        if metrics:
            # Use the most recent or max? Assuming one per drug for now.
            chem_score = metrics[0].get("chem_score", 0) or 0
            
        bio_score = record.get("bio_score") or 0
        tract_score = record.get("tractability_score") or 0
        
        # Weights
        w_bio = 0.5
        w_chem = 0.3
        w_tract = 0.2
        
        # Renormalize if missing data (simplified)
        # If chem_score is 0 (missing), distribute weight?
        # For now, let's keep it simple as per spec:
        # "Apply caps (biology floor, tractability floor)"
        
        total_raw = (w_bio * bio_score) + (w_chem * chem_score) + (w_tract * tract_score)
        
        # Floors
        if bio_score == 0:
            total_raw = min(total_raw, 30)
            
        if tract_score <= 20:
            total_raw = min(total_raw, 50)
            
        total_score = max(0, min(100, total_raw))
        
        # Update
        supabase_client.supabase.table("epi_scores").update({
            "chem_score": chem_score,
            "total_score": total_score
        }).eq("id", record["id"]).execute()
        
        print(f"  ✅ Updated TotalScore for {record['id']}: {total_score:.1f}")

if __name__ == "__main__":
    run()
