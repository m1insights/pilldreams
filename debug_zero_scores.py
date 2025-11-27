import os
import sys
import json
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.etl import supabase_client, open_targets, config

def debug_zero_scores():
    load_dotenv()
    if not supabase_client.supabase:
        print("Supabase client not initialized.")
        return

    # 1. Find an asset with score 0
    print("Fetching an asset with score 0...")
    response = supabase_client.supabase.table("pipeline_assets").select("*, pipeline_asset_targets(*)").eq("relative_score", 0).limit(1).execute()
    
    if not response.data:
        print("No assets with score 0 found.")
        return

    asset = response.data[0]
    print(f"Asset: {asset['name']} (ID: {asset['id']})")
    
    if not asset['pipeline_asset_targets']:
        print("No targets linked to this asset.")
        return

    target = asset['pipeline_asset_targets'][0]
    target_id = target['ot_target_id']
    print(f"Target ID: {target_id} ({target['approved_symbol']})")

    # 2. Check Indication
    # We need to know which disease this asset was fetched for to check the score.
    # We can check pipeline_asset_indications
    indications = supabase_client.supabase.table("pipeline_asset_indications").select("*").eq("pipeline_asset_id", asset['id']).execute().data
    if not indications:
        print("No indications found.")
        return
    
    efo_id = indications[0]['efo_disease_id']
    print(f"Disease: {indications[0]['disease_name']} ({efo_id})")

    # 3. Fetch scores for this disease from OT
    print(f"Fetching top targets for {efo_id} from Open Targets...")
    scores = open_targets.fetch_disease_targets_scores(efo_id)
    
    print(f"Fetched {len(scores)} targets with scores.")
    
    if target_id in scores:
        print(f"✅ Target {target_id} found in scores. Score: {scores[target_id]}")
    else:
        print(f"❌ Target {target_id} NOT found in fetched scores.")
        # Check if we can find it if we fetch MORE
        # Or maybe the query is limited?

if __name__ == "__main__":
    debug_zero_scores()
