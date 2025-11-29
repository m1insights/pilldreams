from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    # Fallback for local development or if env vars are missing during init
    print("Warning: SUPABASE_URL or SUPABASE_SERVICE_KEY not set.")
    supabase = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upsert_epi_target(data: dict) -> str:
    """Insert or update epi_target, return id."""
    if not supabase: return None
    # Assuming symbol is unique enough for upsert, or we use on_conflict on symbol?
    # The schema doesn't strictly enforce unique symbol but it should be.
    # Let's assume we upsert on symbol if we can, or just insert.
    # Actually, for seeding, we might want to check existence.
    # For now, let's use upsert on 'symbol' if we add a unique constraint, 
    # but the schema didn't have one explicitly in the CREATE TABLE (just index).
    # Let's try to upsert on 'symbol' if possible, or just insert if not exists.
    # Supabase upsert requires a unique constraint.
    # We should probably add a unique constraint to symbol in the migration if we want to upsert.
    # For now, let's just insert and ignore conflicts or handle manually.
    
    # Better: Select by symbol, if exists return id, else insert.
    existing = supabase.table("epi_targets").select("id").eq("symbol", data["symbol"]).execute()
    if existing.data:
        # Update?
        supabase.table("epi_targets").update(data).eq("id", existing.data[0]["id"]).execute()
        return existing.data[0]["id"]
    else:
        result = supabase.table("epi_targets").insert(data).execute()
        return result.data[0]["id"]

def upsert_epi_drug(data: dict) -> str:
    """Insert or update epi_drug, return id."""
    if not supabase: return None
    # Match on name or chembl_id or ot_drug_id
    # Let's try matching on name first for the gold set seeding
    existing = supabase.table("epi_drugs").select("id").eq("name", data["name"]).execute()
    if existing.data:
        supabase.table("epi_drugs").update(data).eq("id", existing.data[0]["id"]).execute()
        return existing.data[0]["id"]
    else:
        result = supabase.table("epi_drugs").insert(data).execute()
        return result.data[0]["id"]

def insert_epi_drug_target(data: dict):
    if not supabase: return
    # Check if exists to avoid duplicates
    existing = supabase.table("epi_drug_targets").select("id")\
        .eq("drug_id", data["drug_id"])\
        .eq("target_id", data["target_id"]).execute()
    if not existing.data:
        supabase.table("epi_drug_targets").insert(data).execute()

def insert_epi_indication(data: dict) -> str:
    if not supabase: return None
    # Match on name or efo_id
    if data.get("efo_id"):
        existing = supabase.table("epi_indications").select("id").eq("efo_id", data["efo_id"]).execute()
    else:
        existing = supabase.table("epi_indications").select("id").eq("name", data["name"]).execute()
        
    if existing.data:
        return existing.data[0]["id"]
    else:
        result = supabase.table("epi_indications").insert(data).execute()
        return result.data[0]["id"]

def insert_epi_drug_indication(data: dict):
    if not supabase: return
    existing = supabase.table("epi_drug_indications").select("id")\
        .eq("drug_id", data["drug_id"])\
        .eq("indication_id", data["indication_id"]).execute()
    if not existing.data:
        supabase.table("epi_drug_indications").insert(data).execute()

def upsert_epi_scores(data: dict):
    if not supabase: return
    # Match on drug_id + indication_id
    existing = supabase.table("epi_scores").select("id")\
        .eq("drug_id", data["drug_id"])\
        .eq("indication_id", data["indication_id"]).execute()
    if existing.data:
        supabase.table("epi_scores").update(data).eq("id", existing.data[0]["id"]).execute()
    else:
        supabase.table("epi_scores").insert(data).execute()

def upsert_epi_signature(data: dict) -> str:
    if not supabase: return None
    existing = supabase.table("epi_signatures").select("id").eq("name", data["name"]).execute()
    if existing.data:
        supabase.table("epi_signatures").update(data).eq("id", existing.data[0]["id"]).execute()
        return existing.data[0]["id"]
    else:
        result = supabase.table("epi_signatures").insert(data).execute()
        return result.data[0]["id"]

def insert_epi_signature_target(data: dict):
    if not supabase: return
    existing = supabase.table("epi_signature_targets").select("id")\
        .eq("signature_id", data["signature_id"])\
        .eq("target_id", data["target_id"]).execute()
    if not existing.data:
        supabase.table("epi_signature_targets").insert(data).execute()

def insert_chembl_metrics(data: dict):
    if not supabase: return
    supabase.table("chembl_metrics").insert(data).execute()

# ============================================================
# Epigenetic Editing Asset Functions
# ============================================================

def upsert_editing_asset(data: dict) -> str:
    """Insert or update epi_editing_asset, return id."""
    if not supabase: return None
    # Match on name (should be unique program name)
    existing = supabase.table("epi_editing_assets").select("id").eq("name", data["name"]).execute()
    if existing.data:
        supabase.table("epi_editing_assets").update(data).eq("id", existing.data[0]["id"]).execute()
        return existing.data[0]["id"]
    else:
        result = supabase.table("epi_editing_assets").insert(data).execute()
        return result.data[0]["id"]

def upsert_editing_target_gene(data: dict) -> str:
    """Insert or update epi_editing_target_genes, return id."""
    if not supabase: return None
    existing = supabase.table("epi_editing_target_genes").select("id").eq("symbol", data["symbol"]).execute()
    if existing.data:
        supabase.table("epi_editing_target_genes").update(data).eq("id", existing.data[0]["id"]).execute()
        return existing.data[0]["id"]
    else:
        result = supabase.table("epi_editing_target_genes").insert(data).execute()
        return result.data[0]["id"]

def insert_editing_asset_target(data: dict):
    """Link editing asset to target gene."""
    if not supabase: return
    existing = supabase.table("epi_editing_asset_targets").select("id")\
        .eq("editing_asset_id", data["editing_asset_id"])\
        .eq("target_gene_id", data["target_gene_id"]).execute()
    if not existing.data:
        supabase.table("epi_editing_asset_targets").insert(data).execute()

def upsert_editing_scores(data: dict):
    """Insert or update epi_editing_scores."""
    if not supabase: return
    existing = supabase.table("epi_editing_scores").select("id")\
        .eq("editing_asset_id", data["editing_asset_id"]).execute()
    if existing.data:
        supabase.table("epi_editing_scores").update(data).eq("id", existing.data[0]["id"]).execute()
    else:
        supabase.table("epi_editing_scores").insert(data).execute()

def get_editing_target_gene_by_symbol(symbol: str):
    """Get editing target gene by symbol."""
    if not supabase: return None
    result = supabase.table("epi_editing_target_genes").select("*").eq("symbol", symbol).execute()
    return result.data[0] if result.data else None

def get_all_editing_assets():
    """Get all editing assets."""
    if not supabase: return []
    return supabase.table("epi_editing_assets").select("*").execute().data

def get_epi_target_by_symbol(symbol: str):
    """Get epi target by symbol."""
    if not supabase: return None
    result = supabase.table("epi_targets").select("*").eq("symbol", symbol).execute()
    return result.data[0] if result.data else None

def get_all_drug_indications():
    if not supabase: return []
    # Join with drugs to get drug name if needed, but IDs are enough
    return supabase.table("epi_drug_indications").select("*").execute().data

def get_drug_targets(drug_id: str):
    if not supabase: return []
    return supabase.table("epi_drug_targets").select("target_id, is_primary_target").eq("drug_id", drug_id).execute().data

def get_epi_target(target_id: str):
    if not supabase: return None
    return supabase.table("epi_targets").select("ot_target_id, symbol").eq("id", target_id).single().execute().data

