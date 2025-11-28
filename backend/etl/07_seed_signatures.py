import sys
import os
from backend.etl import supabase_client

# Ensure we can import backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

def run():
    print("🎼 Seeding Signatures (DREAM Complex)...")
    
    if not supabase_client.supabase:
        print("❌ Supabase client not initialized.")
        return

    # 1. Create Signature
    sig_data = {
        "name": "DREAM_complex",
        "category": "transcriptional_complex",
        "description": "Cell-cycle/quiescence transcriptional repressor complex (DP, RB-like, E2F, MuvB). Influences expression of proliferation genes and intersects with epigenetic regulation."
    }
    sig_id = supabase_client.upsert_epi_signature(sig_data)
    print(f"Created/Updated DREAM Complex (ID: {sig_id})")
    
    # 2. Add Targets
    # Map of Symbol -> Role
    components = {
        "RBL1": "core_subunit",
        "RBL2": "core_subunit",
        "E2F4": "core_subunit",
        "E2F5": "core_subunit",
        "TFDP1": "core_subunit",
        "TFDP2": "core_subunit",
        "LIN9": "core_subunit",
        "LIN37": "core_subunit",
        "LIN52": "core_subunit",
        "LIN54": "core_subunit",
        "RBBP4": "core_subunit"
    }
    
    for symbol, role in components.items():
        # Find Target ID
        target = supabase_client.supabase.table("epi_targets").select("id").eq("symbol", symbol).execute().data
        
        if not target:
            print(f"  ⚠️ Target {symbol} not found in DB. Skipping link.")
            # In a real scenario, we might want to seed these non-epi targets too if they are missing.
            # For now, we only seeded the "seed_epi_targets.csv" list.
            # We should probably upsert them as "associated" targets if missing?
            # Let's skip for now to keep it clean, or add them to the seed list.
            continue
            
        target_id = target[0]["id"]
        
        supabase_client.insert_epi_signature_target({
            "signature_id": sig_id,
            "target_id": target_id,
            "role": role
        })
        print(f"  Linked {symbol} to DREAM complex.")

if __name__ == "__main__":
    run()
