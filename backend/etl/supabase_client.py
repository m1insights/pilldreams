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

def upsert_drug(data: dict) -> int:
    """Insert or update drug, return drug.id."""
    if not supabase: return -1
    result = supabase.table("drugs").upsert(
        data, on_conflict="ot_drug_id"
    ).execute()
    return result.data[0]["id"]

def insert_drug_indication(drug_id: int, efo_id: str, name: str, phase: str):
    if not supabase: return
    supabase.table("drug_indications").insert({
        "drug_id": drug_id,
        "efo_disease_id": efo_id,
        "disease_name": name,
        "phase": phase
    }).execute()

def insert_drug_target(drug_id: int, target_data: dict):
    if not supabase: return
    supabase.table("drug_targets").insert({
        "drug_id": drug_id,
        **target_data
    }).execute()

def upsert_pipeline_asset(data: dict) -> int:
    """Insert or update pipeline asset, return id."""
    if not supabase: return -1
    result = supabase.table("pipeline_assets").upsert(
        data, on_conflict="ot_drug_id"
    ).execute()
    return result.data[0]["id"]

def insert_pipeline_asset_indication(asset_id: int, efo_id: str, name: str, phase: str):
    if not supabase: return
    supabase.table("pipeline_asset_indications").insert({
        "pipeline_asset_id": asset_id,
        "efo_disease_id": efo_id,
        "disease_name": name,
        "phase": phase
    }).execute()

def insert_pipeline_asset_target(asset_id: int, target_data: dict):
    if not supabase: return
    supabase.table("pipeline_asset_targets").insert({
        "pipeline_asset_id": asset_id,
        **target_data
    }).execute()

def insert_chembl_metrics(data: dict):
    if not supabase: return
    # We might link to drug_id OR pipeline_asset_id. 
    # The data dict should contain one of them.
    supabase.table("chembl_metrics").insert(data).execute()

def insert_target_biology_metrics(data: dict):
    if not supabase: return
    supabase.table("target_biology_metrics").upsert(
        data, on_conflict="ot_target_id"
    ).execute()
