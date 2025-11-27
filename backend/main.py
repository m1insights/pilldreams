from fastapi import FastAPI, BackgroundTasks
from etl import config, open_targets, supabase_client, enrichment, chembl
import requests

app = FastAPI()

@app.post("/etl/fetch-known-drugs")
def trigger_etl(background_tasks: BackgroundTasks):
    """Trigger full ETL pipeline in background."""
    background_tasks.add_task(run_full_etl)
    return {"status": "ETL started"}

def run_full_etl():
    """Step 1: Fetch known drugs from Open Targets."""
    print("Starting ETL...")
    for efo_id, disease_name in config.DISEASE_SCOPE.items():
        print(f"Fetching drugs for {disease_name}...")
        rows = open_targets.fetch_known_drugs_for_disease(efo_id)
        
        for row in rows:
            # Filter: small molecules only, phase 3+ or approved
            if row.get("drugType") != "Small molecule":
                continue
            # OT returns phase as int usually, need to check. Assuming int based on typical OT response
            if row.get("phase") not in [3, 4]: 
                continue
            
            drug = row["drug"]
            
            # Upsert drug
            drug_id = supabase_client.upsert_drug({
                "ot_drug_id": drug["id"],
                "name": drug["name"],
                "drug_type": row["drugType"],
                "max_phase": str(row["phase"])
            })
            
            if drug_id == -1: continue

            # Link indication
            supabase_client.insert_drug_indication(
                drug_id, efo_id, disease_name, str(row["phase"])
            )
            
            # Link target
            if row.get("target"):
                supabase_client.insert_drug_target(drug_id, {
                    "ot_target_id": row["target"]["id"],
                    "approved_symbol": row["target"]["approvedSymbol"],
                    "mechanism_of_action": row.get("mechanismOfAction")
                })

            # Fetch ChEMBL Metrics for Gold Set
            # Note: Gold Set drugs are approved, so they should have plenty of data.
            print(f"    Fetching ChEMBL data for {drug['name']}...")
            chembl_metrics = chembl.fetch_chembl_activity(drug["id"], None) # No target filter for now
            
            if chembl_metrics:
                # Calculate ChemScore (Same logic)
                potency_score = 0
                p_best = chembl_metrics.get("p_act_best")
                if p_best:
                    if p_best >= 8: potency_score = 40
                    elif p_best >= 7: potency_score = 30
                    elif p_best >= 6: potency_score = 20
                    else: potency_score = 10
                
                selectivity_score = 0
                delta_p = chembl_metrics.get("delta_p")
                if delta_p is not None:
                    if delta_p >= 2: selectivity_score = 30
                    elif delta_p >= 1: selectivity_score = 20
                    elif delta_p >= 0: selectivity_score = 10
                
                richness_score = 0
                n_prim = chembl_metrics.get("n_activities_primary", 0)
                n_tot = chembl_metrics.get("n_activities_total", 0)
                if n_prim >= 10 and n_tot >= 30: richness_score = 30
                elif n_prim >= 3 or n_tot >= 10: richness_score = 20
                elif n_tot > 0: richness_score = 10
                
                chem_score = potency_score + selectivity_score + richness_score
                chembl_metrics["chem_score"] = chem_score
                
                # Insert Metrics linked to drug_id
                chembl_metrics["drug_id"] = drug_id
                supabase_client.insert_chembl_metrics(chembl_metrics)
    print("ETL Complete.")

@app.post("/etl/fetch-pipeline-assets")
def trigger_pipeline_etl(background_tasks: BackgroundTasks):
    """Trigger pipeline assets ETL."""
    background_tasks.add_task(run_pipeline_etl)
    return {"status": "Pipeline ETL started"}

def run_pipeline_etl():
    """Fetch Phase 1-2 drugs and score them."""
    print("Starting Pipeline ETL...")
    for efo_id, disease_name in config.DISEASE_SCOPE.items():
        print(f"Processing {disease_name}...")
        
        # 1. Fetch Target-Disease Scores for scoring
        print(f"  Fetching target scores...")
        target_scores = open_targets.fetch_disease_targets_scores(efo_id)
        
        # 2. Fetch Drugs
        print(f"  Fetching drugs...")
        rows = open_targets.fetch_known_drugs_for_disease(efo_id)
        
        for row in rows:
            # Filter: Small molecule, Phase 1 or 2
            if row.get("drugType") != "Small molecule":
                continue
            
            phase = row.get("phase")
            # OT phase can be int or None. 
            # We want Phase 1 or 2. 
            # Note: OT might return max phase for the drug generally, or phase for the indication? 
            # The query in open_targets.py fetches `phase` from `knownDrugs` row, which is the phase for THAT disease.
            if phase not in [1, 2]:
                continue
                
            drug = row["drug"]
            
            # Filter: Exclude globally approved drugs (Phase 4)
            # We want true pipeline assets, not repurposing of approved drugs.
            if drug.get("maximumClinicalTrialPhase") == 4:
                continue
            
            # Calculate Score
            # Average score of targets linked to this drug for this disease
            # The row has `target` (single). `knownDrugs` row connects Drug-Disease-Target.
            # So we just take the score for THIS target.
            target_id = row["target"]["id"]
            evidence_score = target_scores.get(target_id, 0.0)
            
            # Upsert Pipeline Asset
            asset_id = supabase_client.upsert_pipeline_asset({
                "ot_drug_id": drug["id"],
                "name": drug["name"],
                "phase": str(phase),
                "target_evidence_score": evidence_score,
                "relative_score": evidence_score * 100 # Simple V1: 0-100 scale based on evidence
            })
            
            if asset_id == -1: continue

            # Link Indication
            supabase_client.insert_pipeline_asset_indication(
                asset_id, efo_id, disease_name, str(phase)
            )
            
            # Link Target
            supabase_client.insert_pipeline_asset_target(asset_id, {
                "ot_target_id": target_id,
                "approved_symbol": row["target"]["approvedSymbol"],
                "mechanism_of_action": row.get("mechanismOfAction")
            })

            # 3. Fetch ChEMBL Metrics (Chemistry Quality)
            # ... (Existing ChEMBL logic) ...
            # For now, let's fetch target details to get dbXrefs AND Tractability.
            target_details = open_targets.fetch_target_details(target_id)
            
            # 4. Process Tractability (UniProt/OT Layer)
            # Fetch via REST API because GraphQL schema is tricky
            tractability = []
            try:
                t_resp = requests.get(f"https://api.platform.opentargets.org/api/v4/target/{target_id}")
                if t_resp.status_code == 200:
                    t_data = t_resp.json()
                    tractability = t_data.get("tractability", [])
            except Exception as e:
                print(f"    ❌ Error fetching tractability for {target_id}: {e}")

            sm_bucket = None
            ab_bucket = None
            
            # Parse buckets
            # OT returns list of {id: "Small molecule tractability bucket 1", value: true/false} or similar?
            # Actually, the API returns: [{id: "Small molecule tractability bucket 1", modality: "SM", value: "True"}, ...]
            # We need to find the lowest bucket number (highest tractability) for SM and AB.
            
            for t in tractability:
                # if t.get("value") != "True": continue
                
                tid = t.get("id", "")
                # Example ID: "Small molecule tractability bucket 1"
                if "Small molecule tractability bucket" in tid:
                    try:
                        bucket_num = int(tid.split("bucket")[-1].strip())
                        if sm_bucket is None or bucket_num < sm_bucket:
                            sm_bucket = bucket_num
                    except: pass
                elif "Antibody tractability bucket" in tid:
                    try:
                        bucket_num = int(tid.split("bucket")[-1].strip())
                        if ab_bucket is None or bucket_num < ab_bucket:
                            ab_bucket = bucket_num
                    except: pass

            # Calculate Tractability Score (0-100)
            # Bucket 1: 100, Bucket 2: 90, Bucket 3: 80, ... Bucket 8: 30
            tract_score = 0
            if sm_bucket:
                # Formula: 110 - (10 * bucket) -> Bucket 1 = 100, Bucket 10 = 10
                score = 110 - (10 * sm_bucket)
                tract_score = max(0, min(100, score))
            elif ab_bucket:
                 # Fallback to antibody if no SM? Or separate?
                 # For now, focus on SM since we filter for Small Molecules.
                 pass
            
            # Insert Target Biology Metrics
            supabase_client.insert_target_biology_metrics({
                "ot_target_id": target_id,
                "small_molecule_tractability_bucket": sm_bucket,
                "antibody_tractability_bucket": ab_bucket,
                "tractability_score": tract_score
            })

            # --- SCORING V2: Weighted Model ---
            
            # 1. BioScore (0-100)
            # Based on OT evidence score (0-1).
            bio_score = min(100, evidence_score * 100)
            
            # 2. ChemScore (0-100)
            # Calculated from ChEMBL metrics below.
            # We need to fetch them first or calculate them here if we have them.
            # Wait, we fetch ChEMBL *after* this block in the original code.
            # We should move ChEMBL fetching UP or do it here.
            
            print(f"    Fetching ChEMBL data for {drug['name']}...")
            chembl_metrics = chembl.fetch_chembl_activity(drug["id"], None)
            
            chem_score = 0
            has_chem_data = False
            
            if chembl_metrics:
                has_chem_data = True
                # Potency (0-40)
                potency_score = 0
                p_best = chembl_metrics.get("p_act_best")
                if p_best:
                    if p_best >= 9: potency_score = 40
                    elif p_best >= 8: potency_score = 35
                    elif p_best >= 7: potency_score = 25
                    elif p_best >= 6: potency_score = 15
                    else: potency_score = 5
                
                # Selectivity (0-30)
                selectivity_score = 0
                delta_p = chembl_metrics.get("delta_p")
                if delta_p is not None:
                    if delta_p >= 2: selectivity_score = 30
                    elif delta_p >= 1: selectivity_score = 20
                    elif delta_p >= 0: selectivity_score = 10
                
                # Richness (0-30)
                richness_score = 0
                n_prim = chembl_metrics.get("n_activities_primary", 0)
                n_tot = chembl_metrics.get("n_activities_total", 0)
                if n_prim >= 10 and n_tot >= 30: richness_score = 30
                elif (n_prim >= 3 and n_prim <= 9) or (n_tot >= 10 and n_tot <= 29): richness_score = 20
                elif n_tot > 0: richness_score = 10
                
                chem_score = potency_score + selectivity_score + richness_score
                chem_score = min(100, chem_score)
                
                # Insert Metrics
                chembl_metrics["pipeline_asset_id"] = asset_id
                chembl_metrics["chem_score"] = chem_score
                supabase_client.insert_chembl_metrics(chembl_metrics)
            
            # 3. TractabilityScore (0-100)
            # Calculated above as `tract_score`.
            
            # 4. TotalScore Calculation
            w_bio = 0.5
            w_chem = 0.3
            w_tract = 0.2
            
            # Handle missing data (Renormalization)
            if not has_chem_data:
                # Distribute w_chem to bio and tract
                denom = w_bio + w_tract
                w_bio = w_bio / denom
                w_tract = w_tract / denom
                w_chem = 0
                chem_score = 0
            
            # If tractability is missing (score 0? or check bucket?)
            # If bucket is None, we treat as missing? Or low score?
            # User recipe: "If TractabilityScore is None... renormalize".
            # Our logic sets tract_score to 0 if no bucket.
            # Let's assume if sm_bucket is None, it's missing.
            if sm_bucket is None:
                 # Distribute w_tract to bio and chem
                 denom = w_bio + w_chem
                 if denom > 0:
                    w_bio = w_bio / denom
                    w_chem = w_chem / denom
                    w_tract = 0
                    tract_score = 0
            
            total_raw = (w_bio * bio_score) + (w_chem * chem_score) + (w_tract * tract_score)
            
            # Floors / Caps
            # Biology Floor
            if bio_score == 0:
                total_raw = min(total_raw, 30)
            
            # Tractability Floor
            if tract_score <= 20:
                total_raw = min(total_raw, 50)
                
            total_score = max(0, min(100, total_raw))
            
            # Update Pipeline Asset with Scores
            supabase_client.upsert_pipeline_asset({
                "ot_drug_id": drug["id"],
                "name": drug["name"],
                "phase": str(phase),
                "target_evidence_score": evidence_score,
                "relative_score": evidence_score * 100, # Legacy
                "bio_score": bio_score,
                "chem_score": chem_score if has_chem_data else None,
                "tractability_score": tract_score if sm_bucket else None,
                "total_score": total_score
            })
            
    print("Pipeline ETL Complete.")

@app.post("/etl/enrich-drugs")
def trigger_enrichment(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_enrichment)
    return {"status": "Enrichment started"}

def run_enrichment():
    if not supabase_client.supabase: return
    # Fetch all drugs
    drugs = supabase_client.supabase.table("drugs").select("id, name").execute().data
    for drug in drugs:
        print(f"Enriching {drug['name']}...")
        pubmed_count = enrichment.fetch_pubmed_count(drug["name"])
        openfda_stats = enrichment.fetch_openfda_stats(drug["name"])
        
        supabase_client.supabase.table("drugs").update({
            "pubmed_count": pubmed_count,
            "openfda_ae_count": openfda_stats["count"],
            "serious_ae_ratio": openfda_stats["serious_ae_ratio"]
        }).eq("id", drug["id"]).execute()
    print("Enrichment Complete.")

@app.get("/drugs")
def get_drugs(gold_set_only: bool = False):
    """Return all drugs or gold set only."""
    if not supabase_client.supabase:
        return []
    query = supabase_client.supabase.table("drugs").select("*")
    if gold_set_only:
        query = query.eq("is_gold_set", True)
    return query.execute().data

@app.get("/drugs/{drug_id}/targets")
def get_drug_targets(drug_id: int):
    if not supabase_client.supabase:
        return []
    return supabase_client.supabase.table("drug_targets").select("*").eq("drug_id", drug_id).execute().data

@app.get("/pipeline-assets")
def get_pipeline_assets():
    """Return all pipeline assets."""
    if not supabase_client.supabase:
        return []
    return supabase_client.supabase.table("pipeline_assets").select("*").execute().data

@app.get("/pipeline-assets/{asset_id}/targets")
def get_pipeline_asset_targets(asset_id: int):
    if not supabase_client.supabase:
        return []
    return supabase_client.supabase.table("pipeline_asset_targets").select("*").eq("pipeline_asset_id", asset_id).execute().data
