"""
Targeted script to compute BioScore & TractabilityScore for 3 missing drugs:
- IADADEMSTAT
- PELABRESIB
- REVUMENIB
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from backend.etl import open_targets, supabase_client

MISSING_DRUGS = ['IADADEMSTAT', 'PELABRESIB', 'REVUMENIB']

def run():
    print("🧬 Computing scores for 3 missing drugs...")

    if not supabase_client.supabase:
        print("❌ Supabase client not initialized.")
        return

    # Label scores for tractability
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

    for drug_name in MISSING_DRUGS:
        print(f"\n📦 Processing {drug_name}...")

        # Get drug
        drug = supabase_client.supabase.table("epi_drugs").select("id, name").ilike("name", drug_name).single().execute().data
        if not drug:
            print(f"  ❌ Drug not found: {drug_name}")
            continue

        drug_id = drug["id"]

        # Get drug-indication pairs
        pairs = supabase_client.supabase.table("epi_drug_indications").select("id, indication_id").eq("drug_id", drug_id).execute().data

        if not pairs:
            print(f"  ⚠️ No indications for {drug_name}")
            continue

        # Get drug targets
        targets = supabase_client.get_drug_targets(drug_id)
        print(f"  Targets: {len(targets)}")

        for pair in pairs:
            indication_id = pair["indication_id"]

            # Get indication EFO ID
            indication = supabase_client.supabase.table("epi_indications").select("efo_id, name").eq("id", indication_id).single().execute().data
            efo_id = indication["efo_id"]
            print(f"  Indication: {indication['name']} ({efo_id})")

            # --- BioScore ---
            print(f"    Fetching disease associations for {efo_id}...")
            disease_scores = open_targets.fetch_disease_targets_scores(efo_id)

            bio_score_raw = 0.0
            for t in targets:
                t_info = supabase_client.get_epi_target(t["target_id"])
                if not t_info:
                    continue
                ot_tid = t_info.get("ot_target_id")
                if ot_tid:
                    score = disease_scores.get(ot_tid, 0.0)
                    print(f"      {t_info['symbol']}: association score = {score}")
                    if score > bio_score_raw:
                        bio_score_raw = score

            bio_score = min(100, bio_score_raw * 100)
            print(f"    BioScore: {bio_score:.1f}")

            # --- TractabilityScore ---
            tract_score_max = 0
            for t in targets:
                t_info = supabase_client.get_epi_target(t["target_id"])
                if not t_info:
                    continue
                ot_tid = t_info.get("ot_target_id")
                if not ot_tid:
                    print(f"      {t_info['symbol']}: No OT target ID")
                    continue

                print(f"    Fetching tractability for {t_info['symbol']}...")
                tract_data = open_targets.fetch_tractability(ot_tid)

                ts = 0
                for item in tract_data:
                    if item.get("modality") == "SM" and item.get("value") is True:
                        label = item.get("label", "")
                        if label in label_scores:
                            ts = max(ts, label_scores[label])

                if ts > tract_score_max:
                    tract_score_max = ts
                print(f"      Tractability: {ts}")

            print(f"    TractabilityScore: {tract_score_max}")

            # Upsert score
            score_data = {
                "drug_id": drug_id,
                "indication_id": indication_id,
                "bio_score": bio_score,
                "tractability_score": tract_score_max
            }
            supabase_client.upsert_epi_scores(score_data)
            print(f"  ✅ Saved scores for {drug_name}: Bio={bio_score:.1f}, Tract={tract_score_max}")

    print("\n✅ Done computing scores for missing drugs!")

if __name__ == "__main__":
    run()
