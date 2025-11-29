"""
Epigenetics Oncology Intelligence API Endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
from backend.etl.supabase_client import supabase

router = APIRouter(prefix="/epi", tags=["Epigenetics"])


# ============ Pydantic Models ============

class TargetSummary(BaseModel):
    id: str  # UUID
    symbol: str
    name: Optional[str] = None
    family: str
    target_class: str
    asset_count: int = 0
    avg_bio_score: Optional[float] = None
    avg_tractability_score: Optional[float] = None


class TargetDetail(BaseModel):
    id: str  # UUID
    symbol: str
    full_name: Optional[str] = None
    family: str
    target_class: str = "Unknown"
    ot_target_id: Optional[str] = None
    uniprot_id: Optional[str] = None
    ensembl_id: Optional[str] = None


class DrugSummary(BaseModel):
    id: str  # UUID
    name: str
    chembl_id: Optional[str] = None
    drug_type: Optional[str] = None
    fda_approved: bool = False
    max_phase: Optional[int] = None  # Clinical phase (1-4)
    total_score: Optional[float] = None
    bio_score: Optional[float] = None
    chem_score: Optional[float] = None
    tractability_score: Optional[float] = None


class DrugDetail(BaseModel):
    id: str  # UUID
    name: str
    chembl_id: Optional[str] = None
    drug_type: Optional[str] = None
    fda_approved: bool = False
    first_approval_date: Optional[str] = None
    source: Optional[str] = None


class ScoreBreakdown(BaseModel):
    drug_id: str  # UUID
    drug_name: str
    indication_id: str  # UUID
    indication_name: str
    bio_score: Optional[float] = None
    chem_score: Optional[float] = None
    tractability_score: Optional[float] = None
    total_score: Optional[float] = None


class IndicationSummary(BaseModel):
    id: str  # UUID
    name: str
    efo_id: Optional[str] = None
    disease_area: Optional[str] = None
    drug_count: int = 0


class SearchResult(BaseModel):
    type: str  # 'target', 'drug', 'indication'
    id: str  # UUID
    name: str
    subtitle: str
    score: Optional[float] = None


# ============ Targets Endpoints ============

@router.get("/targets", response_model=List[TargetSummary])
async def list_targets(
    family: Optional[str] = None,
    target_class: Optional[str] = None
):
    """List all epigenetic targets with optional filtering."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    query = supabase.table("epi_targets").select("*")

    if family:
        query = query.eq("family", family)
    if target_class:
        query = query.eq("class", target_class)

    targets = query.execute().data

    # Get drug counts and scores for each target
    result = []
    for t in targets:
        # Count drugs linked to this target
        drug_links = supabase.table("epi_drug_targets")\
            .select("drug_id")\
            .eq("target_id", t["id"]).execute().data

        asset_count = len(drug_links)

        # Get average scores for drugs targeting this target
        avg_bio = None
        avg_tract = None
        if drug_links:
            drug_ids = [d["drug_id"] for d in drug_links]
            scores = supabase.table("epi_scores")\
                .select("bio_score, tractability_score")\
                .in_("drug_id", drug_ids).execute().data

            bio_scores = [s["bio_score"] for s in scores if s.get("bio_score")]
            tract_scores = [s["tractability_score"] for s in scores if s.get("tractability_score")]

            if bio_scores:
                avg_bio = sum(bio_scores) / len(bio_scores)
            if tract_scores:
                avg_tract = sum(tract_scores) / len(tract_scores)

        result.append(TargetSummary(
            id=t["id"],
            symbol=t["symbol"],
            name=t.get("full_name"),
            family=t["family"],
            target_class=t.get("class", "Unknown"),
            asset_count=asset_count,
            avg_bio_score=round(avg_bio, 1) if avg_bio else None,
            avg_tractability_score=round(avg_tract, 1) if avg_tract else None
        ))

    return result


@router.get("/targets/{target_id}")
async def get_target(target_id: str):
    """Get detailed target information with associated drugs and signatures."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    # Get target
    target_result = supabase.table("epi_targets")\
        .select("*")\
        .eq("id", target_id)\
        .single().execute()

    if not target_result.data:
        raise HTTPException(status_code=404, detail="Target not found")

    target = target_result.data

    # Get associated drugs via drug_targets
    drugs = supabase.table("epi_drug_targets")\
        .select("*, epi_drugs(*)")\
        .eq("target_id", target_id).execute().data

    # Get signatures
    signatures = supabase.table("epi_signature_targets")\
        .select("*, epi_signatures(*)")\
        .eq("target_id", target_id).execute().data

    return {
        "target": TargetDetail(
            id=target["id"],
            symbol=target["symbol"],
            full_name=target.get("full_name"),
            family=target["family"],
            target_class=target.get("class", "Unknown"),
            ot_target_id=target.get("ot_target_id"),
            uniprot_id=target.get("uniprot_id"),
            ensembl_id=target.get("ensembl_id")
        ),
        "drugs": drugs,
        "signatures": signatures
    }


# ============ Drugs Endpoints ============

@router.get("/drugs", response_model=List[DrugSummary])
async def list_drugs(
    target_id: Optional[str] = None,
    indication_id: Optional[str] = None,
    approved_only: bool = False
):
    """List drugs with optional filtering."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    # Base query
    if target_id:
        # Get drugs for specific target
        drug_links = supabase.table("epi_drug_targets")\
            .select("drug_id")\
            .eq("target_id", target_id).execute().data
        drug_ids = [d["drug_id"] for d in drug_links]

        if not drug_ids:
            return []

        query = supabase.table("epi_drugs")\
            .select("*")\
            .in_("id", drug_ids)
    elif indication_id:
        # Get drugs for specific indication
        drug_links = supabase.table("epi_drug_indications")\
            .select("drug_id")\
            .eq("indication_id", indication_id).execute().data
        drug_ids = [d["drug_id"] for d in drug_links]

        if not drug_ids:
            return []

        query = supabase.table("epi_drugs")\
            .select("*")\
            .in_("id", drug_ids)
    else:
        query = supabase.table("epi_drugs").select("*")

    if approved_only:
        query = query.eq("fda_approved", True)

    drugs = query.execute().data

    # Get scores for each drug
    result = []
    for drug in drugs:
        # Get all scores from epi_scores (take max if multiple indications)
        scores = supabase.table("epi_scores")\
            .select("total_score, bio_score, chem_score, tractability_score")\
            .eq("drug_id", drug["id"]).execute().data

        total_score = None
        bio_score = None
        chem_score = None
        tractability_score = None
        if scores:
            # Find the best scoring indication
            valid_scores = [(s.get("total_score"), s) for s in scores if s.get("total_score")]
            if valid_scores:
                best = max(valid_scores, key=lambda x: x[0])
                total_score = best[0]
                bio_score = best[1].get("bio_score")
                chem_score = best[1].get("chem_score")
                tractability_score = best[1].get("tractability_score")

        # Get max_phase from indications
        indications = supabase.table("epi_drug_indications")\
            .select("max_phase")\
            .eq("drug_id", drug["id"]).execute().data
        max_phase = None
        if indications:
            phases = [i.get("max_phase") for i in indications if i.get("max_phase")]
            if phases:
                max_phase = max(phases)

        result.append(DrugSummary(
            id=drug["id"],
            name=drug["name"],
            chembl_id=drug.get("chembl_id"),
            drug_type=drug.get("drug_type"),
            fda_approved=drug.get("fda_approved", False),
            max_phase=max_phase,
            total_score=round(total_score, 1) if total_score else None,
            bio_score=round(bio_score, 1) if bio_score else None,
            chem_score=round(chem_score, 1) if chem_score else None,
            tractability_score=round(tractability_score, 1) if tractability_score else None
        ))

    return result


@router.get("/drugs/{drug_id}")
async def get_drug(drug_id: str):
    """Get detailed drug information with scores and targets."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    # Get drug
    drug_result = supabase.table("epi_drugs")\
        .select("*")\
        .eq("id", drug_id)\
        .single().execute()

    if not drug_result.data:
        raise HTTPException(status_code=404, detail="Drug not found")

    drug = drug_result.data

    # Get targets
    targets = supabase.table("epi_drug_targets")\
        .select("*, epi_targets(*)")\
        .eq("drug_id", drug_id).execute().data

    # Get indications with scores
    indications = supabase.table("epi_drug_indications")\
        .select("*, epi_indications(*)")\
        .eq("drug_id", drug_id).execute().data

    # Get scores
    scores = supabase.table("epi_scores")\
        .select("*, epi_indications(name)")\
        .eq("drug_id", drug_id).execute().data

    # Get chemistry metrics
    chem_metrics = supabase.table("chembl_metrics")\
        .select("*")\
        .eq("drug_id", drug_id).execute().data

    return {
        "drug": DrugDetail(
            id=drug["id"],
            name=drug["name"],
            chembl_id=drug.get("chembl_id"),
            drug_type=drug.get("drug_type"),
            fda_approved=drug.get("fda_approved", False),
            first_approval_date=drug.get("first_approval_date"),
            source=drug.get("source")
        ),
        "targets": targets,
        "indications": indications,
        "scores": scores,
        "chemistry": chem_metrics[0] if chem_metrics else None
    }


# ============ Indications Endpoints ============

@router.get("/indications", response_model=List[IndicationSummary])
async def list_indications():
    """List all indications."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    indications = supabase.table("epi_indications").select("*").execute().data

    result = []
    for ind in indications:
        # Count drugs
        drug_count = len(supabase.table("epi_drug_indications")\
            .select("drug_id")\
            .eq("indication_id", ind["id"]).execute().data)

        result.append(IndicationSummary(
            id=ind["id"],
            name=ind["name"],
            efo_id=ind.get("efo_id"),
            disease_area=ind.get("disease_area"),
            drug_count=drug_count
        ))

    return result


@router.get("/indications/{indication_id}")
async def get_indication(indication_id: str):
    """Get indication details with associated drugs."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    # Get indication
    ind_result = supabase.table("epi_indications")\
        .select("*")\
        .eq("id", indication_id)\
        .single().execute()

    if not ind_result.data:
        raise HTTPException(status_code=404, detail="Indication not found")

    indication = ind_result.data

    # Get drugs with scores for this indication
    drug_indications = supabase.table("epi_drug_indications")\
        .select("*, epi_drugs(*)")\
        .eq("indication_id", indication_id).execute().data

    # Get scores
    scores = supabase.table("epi_scores")\
        .select("*, epi_drugs(name)")\
        .eq("indication_id", indication_id).execute().data

    return {
        "indication": indication,
        "drugs": drug_indications,
        "scores": scores
    }


# ============ Scores Endpoints ============

@router.get("/scores", response_model=List[ScoreBreakdown])
async def list_scores(
    min_total_score: Optional[float] = None,
    min_bio_score: Optional[float] = None
):
    """Get all scores with drug and indication details."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    query = supabase.table("epi_scores")\
        .select("*, epi_drugs(name), epi_indications(name)")

    if min_total_score:
        query = query.gte("total_score", min_total_score)
    if min_bio_score:
        query = query.gte("bio_score", min_bio_score)

    scores = query.execute().data

    return [
        ScoreBreakdown(
            drug_id=s["drug_id"],
            drug_name=s["epi_drugs"]["name"] if s.get("epi_drugs") else "Unknown",
            indication_id=s["indication_id"],
            indication_name=s["epi_indications"]["name"] if s.get("epi_indications") else "Unknown",
            bio_score=s.get("bio_score"),
            chem_score=s.get("chem_score"),
            tractability_score=s.get("tractability_score"),
            total_score=s.get("total_score")
        )
        for s in scores
    ]


# ============ Signatures Endpoints ============

@router.get("/signatures/{name}")
async def get_signature(name: str):
    """Get signature details with member targets."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    # Get signature
    sig_result = supabase.table("epi_signatures")\
        .select("*")\
        .eq("name", name)\
        .single().execute()

    if not sig_result.data:
        raise HTTPException(status_code=404, detail="Signature not found")

    signature = sig_result.data

    # Get member targets
    members = supabase.table("epi_signature_targets")\
        .select("*, epi_targets(*)")\
        .eq("signature_id", signature["id"]).execute().data

    return {
        "signature": signature,
        "members": members
    }


# ============ Search Endpoint ============

@router.get("/search", response_model=List[SearchResult])
async def search_entities(q: str = Query(..., min_length=1)):
    """Search across targets, drugs, and indications."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    results = []
    search_term = q.lower()

    # Search targets
    targets = supabase.table("epi_targets")\
        .select("id, symbol, family")\
        .ilike("symbol", f"%{search_term}%").execute().data

    for t in targets:
        results.append(SearchResult(
            type="target",
            id=t["id"],
            name=t["symbol"],
            subtitle=t["family"]
        ))

    # Search drugs
    drugs = supabase.table("epi_drugs")\
        .select("id, name, drug_type")\
        .ilike("name", f"%{search_term}%").execute().data

    for d in drugs:
        # Get best score
        scores = supabase.table("epi_scores")\
            .select("total_score")\
            .eq("drug_id", d["id"]).execute().data
        best_score = None
        if scores:
            valid = [s["total_score"] for s in scores if s.get("total_score")]
            if valid:
                best_score = max(valid)

        results.append(SearchResult(
            type="drug",
            id=d["id"],
            name=d["name"],
            subtitle=d.get("drug_type") or "Unknown type",
            score=round(best_score, 1) if best_score else None
        ))

    # Search indications
    indications = supabase.table("epi_indications")\
        .select("id, name, disease_area")\
        .ilike("name", f"%{search_term}%").execute().data

    for i in indications:
        results.append(SearchResult(
            type="indication",
            id=i["id"],
            name=i["name"],
            subtitle=i.get("disease_area") or "Oncology"
        ))

    return results


# ============ Stats Endpoint ============

@router.get("/stats")
async def get_stats():
    """Get platform statistics."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    target_count = len(supabase.table("epi_targets").select("id").execute().data)
    drug_count = len(supabase.table("epi_drugs").select("id").execute().data)
    indication_count = len(supabase.table("epi_indications").select("id").execute().data)

    approved_drugs = len(supabase.table("epi_drugs")\
        .select("id")\
        .eq("fda_approved", True).execute().data)

    # Get families distribution
    targets = supabase.table("epi_targets").select("family").execute().data
    families = {}
    for t in targets:
        fam = t["family"]
        families[fam] = families.get(fam, 0) + 1

    return {
        "total_targets": target_count,
        "total_drugs": drug_count,
        "approved_drugs": approved_drugs,
        "total_indications": indication_count,
        "target_families": families
    }
