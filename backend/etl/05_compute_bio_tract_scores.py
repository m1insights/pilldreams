import sys
import os
from backend.etl import open_targets, supabase_client

# Ensure we can import backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

def run():
    print("🧬 Computing BioScore & TractabilityScore...")
    
    if not supabase_client.supabase:
        print("❌ Supabase client not initialized.")
        return

    # 1. Fetch all drug-indication pairs
    pairs = supabase_client.get_all_drug_indications()
    print(f"Found {len(pairs)} drug-indication pairs.")
    
    # Cache for disease scores and tractability to avoid re-fetching
    # disease_id -> {target_id: score}
    disease_score_cache = {}
    # target_id -> tractability_score
    tractability_cache = {}
    
    for pair in pairs:
        drug_id = pair["drug_id"]
        indication_id = pair["indication_id"]
        
        # Get Indication EFO ID
        indication = supabase_client.supabase.table("epi_indications").select("efo_id").eq("id", indication_id).single().execute().data
        efo_id = indication["efo_id"]
        
        # Get Drug Targets
        targets = supabase_client.get_drug_targets(drug_id)
        
        # --- BioScore ---
        # Max association score of any target for this disease
        bio_score_raw = 0.0
        
        if efo_id not in disease_score_cache:
            print(f"Fetching association scores for {efo_id}...")
            disease_score_cache[efo_id] = open_targets.fetch_disease_targets_scores(efo_id)
            
        scores = disease_score_cache[efo_id]
        
        for t in targets:
            # We need OT Target ID
            t_info = supabase_client.get_epi_target(t["target_id"])
            if not t_info: continue
            
            ot_tid = t_info["ot_target_id"]
            score = scores.get(ot_tid, 0.0)
            if score > bio_score_raw:
                bio_score_raw = score
                
        bio_score = min(100, bio_score_raw * 100)
        
        # --- TractabilityScore ---
        # Max tractability of any target
        tract_score_max = 0
        
        for t in targets:
            t_info = supabase_client.get_epi_target(t["target_id"])
            if not t_info: continue
            ot_tid = t_info["ot_target_id"]
            
            if ot_tid not in tractability_cache:
                print(f"Fetching tractability for {t_info['symbol']}...")
                tract_data = open_targets.fetch_tractability(ot_tid)

                # Calculate Score from new Open Targets schema
                # Schema: [{label, modality, value}, ...]
                # Modality "SM" = Small Molecule
                # Score based on best evidence level (higher = more tractable)
                #   "Approved Drug" = 100
                #   "Advanced Clinical" = 90
                #   "Phase 1 Clinical" = 80
                #   "Structure with Ligand" = 70
                #   "High-Quality Ligand" = 60
                #   "High-Quality Pocket" = 50
                #   "Med-Quality Pocket" = 40
                #   "Druggable Family" = 30

                label_scores = {
                    "Approved Drug": 100,
                    "Advanced Clinical": 90,
                    "Phase 1 Clinical": 80,
                    "Structure with Ligand": 70,
                    "High-Quality Ligand": 60,
                    "High-Quality Pocket": 50,
                    "Med-Quality Pocket": 40,
                    "Druggable Family": 30,
                }

                ts = 0
                for item in tract_data:
                    if item.get("modality") == "SM" and item.get("value") is True:
                        label = item.get("label", "")
                        if label in label_scores:
                            ts = max(ts, label_scores[label])

                tractability_cache[ot_tid] = ts
            
            ts = tractability_cache[ot_tid]
            if ts > tract_score_max:
                tract_score_max = ts
                
        # Upsert Scores
        score_data = {
            "drug_id": drug_id,
            "indication_id": indication_id,
            "bio_score": bio_score,
            "tractability_score": tract_score_max
        }
        supabase_client.upsert_epi_scores(score_data)
        print(f"  ✅ Scores for pair {pair['id']}: Bio={bio_score:.1f}, Tract={tract_score_max}")

if __name__ == "__main__":
    run()
