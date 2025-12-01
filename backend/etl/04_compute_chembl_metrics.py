import sys
import os
from backend.etl import chembl, supabase_client

# Ensure we can import backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

def run():
    print("⚗️ Computing ChEMBL Metrics...")
    
    if not supabase_client.supabase:
        print("❌ Supabase client not initialized.")
        return

    # 1. Fetch all drugs
    drugs = supabase_client.supabase.table("epi_drugs").select("id, name, chembl_id").execute().data
    print(f"Found {len(drugs)} drugs to process.")

    for drug in drugs:
        drug_id = drug["id"]
        name = drug["name"]
        chembl_id = drug.get("chembl_id")

        if not chembl_id or not chembl_id.startswith("CHEMBL"):
            print(f"Skipping {name} (Invalid ChEMBL ID: {chembl_id})")
            continue
            
        print(f"Fetching ChEMBL data for {name} ({chembl_id})...")
        
        # Fetch metrics
        # We pass None for target_chembl_id for now to get general promiscuity/activity
        # Or should we fetch specific target activity? 
        # The spec says: "Compute for each drug–primary target pair: p_act_best, delta_p..."
        # But we haven't linked ChEMBL target IDs to our targets yet.
        # For v1, let's compute general drug properties (best potency across ALL targets, selectivity).
        # If we want target-specific, we need to map our targets to ChEMBL target IDs.
        # Open Targets `target` object has `id` (Ensembl). We can get ChEMBL target ID from OT or UniProt.
        # For now, let's stick to the "Global" chemistry score for the drug as implemented in the previous iteration.
        
        metrics = chembl.fetch_chembl_activity(chembl_id, None)
        
        if not metrics:
            print(f"  ⚠️ No metrics found for {name}")
            continue
            
        # Calculate ChemScore (0-100)
        # Rules from spec/previous code:
        # Potency: p_act_best >= 8 -> 40pts, >=7 -> 30, >=6 -> 20
        # Selectivity: delta_p >= 2 -> 30, >=1 -> 20
        # Richness: n_prim/n_tot
        
        potency_score = 0
        p_best = metrics.get("p_act_best")
        if p_best:
            if p_best >= 8: potency_score = 40
            elif p_best >= 7: potency_score = 30
            elif p_best >= 6: potency_score = 20
            else: potency_score = 10
            
        selectivity_score = 0
        delta_p = metrics.get("delta_p")
        if delta_p is not None:
            if delta_p >= 2: selectivity_score = 30
            elif delta_p >= 1: selectivity_score = 20
            elif delta_p >= 0: selectivity_score = 10
            
        richness_score = 0
        n_prim = metrics.get("n_activities_primary", 0)
        n_tot = metrics.get("n_activities_total", 0)
        # Since we didn't filter by primary target in fetch, n_prim might be 0 or same as total if we consider "best" as primary.
        # Let's just use n_tot for richness.
        if n_tot >= 30: richness_score = 30
        elif n_tot >= 10: richness_score = 20
        elif n_tot > 0: richness_score = 10
        
        chem_score = potency_score + selectivity_score + richness_score
        chem_score = min(100, chem_score)
        
        # Insert into DB
        metrics_data = {
            "drug_id": drug_id,
            "p_act_median": metrics.get("p_act_median"),
            "p_act_best": metrics.get("p_act_best"),
            "p_off_best": metrics.get("p_off_best"),
            "delta_p": metrics.get("delta_p"),
            "n_activities_primary": n_prim,
            "n_activities_total": n_tot,
            "chem_score": chem_score
        }
        
        supabase_client.upsert_chembl_metrics(metrics_data)
        print(f"  ✅ Saved metrics for {name} (Score: {chem_score}, pBest: {metrics.get('p_act_best'):.2f})" if metrics.get('p_act_best') else f"  ✅ Saved metrics for {name} (Score: {chem_score})")

if __name__ == "__main__":
    run()
