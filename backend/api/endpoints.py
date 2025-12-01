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
    modality: Optional[str] = None
    fda_approved: bool = False
    max_phase: Optional[int] = None  # Clinical phase (1-4)
    total_score: Optional[float] = None
    bio_score: Optional[float] = None
    chem_score: Optional[float] = None
    tractability_score: Optional[float] = None
    # Target classification for UI badges
    is_core_epigenetic: Optional[bool] = None  # True = core epigenetic target
    target_family: Optional[str] = None  # e.g., "BET", "HDAC", "metabolic"


class DrugDetail(BaseModel):
    id: str  # UUID
    name: str
    chembl_id: Optional[str] = None
    drug_type: Optional[str] = None
    fda_approved: bool = False
    max_phase: Optional[int] = None  # Clinical phase (1-4)
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

        # Get target classification (for UI badges)
        is_core_epigenetic = None
        target_family = None
        target_links = supabase.table("epi_drug_targets")\
            .select("target_id, epi_targets(is_core_epigenetic, family)")\
            .eq("drug_id", drug["id"]).execute().data

        if target_links:
            # Take first target's classification (most drugs have one target)
            first_target = target_links[0].get("epi_targets")
            if first_target:
                is_core_epigenetic = first_target.get("is_core_epigenetic")
                target_family = first_target.get("family")

        result.append(DrugSummary(
            id=drug["id"],
            name=drug["name"],
            chembl_id=drug.get("chembl_id"),
            drug_type=drug.get("drug_type"),
            modality=drug.get("modality"),
            fda_approved=drug.get("fda_approved", False),
            max_phase=drug.get("max_phase"),
            total_score=round(total_score, 1) if total_score else None,
            bio_score=round(bio_score, 1) if bio_score else None,
            chem_score=round(chem_score, 1) if chem_score else None,
            tractability_score=round(tractability_score, 1) if tractability_score else None,
            is_core_epigenetic=is_core_epigenetic,
            target_family=target_family
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
            max_phase=drug.get("max_phase"),
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

    # Search companies
    try:
        companies = supabase.table("epi_companies")\
            .select("id, name, ticker, epi_focus_score")\
            .or_(f"name.ilike.%{search_term}%,ticker.ilike.%{search_term}%").execute().data

        for c in companies:
            subtitle = c.get("ticker") or "Private"
            if c.get("epi_focus_score"):
                subtitle += f" ({c['epi_focus_score']:.0f}% Epi Focus)"
            results.append(SearchResult(
                type="company",
                id=c["id"],
                name=c["name"],
                subtitle=subtitle
            ))
    except Exception:
        pass  # Companies table may not exist

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

    # Get editing asset count (if table exists)
    editing_count = 0
    try:
        editing_count = len(supabase.table("epi_editing_assets").select("id").execute().data)
    except:
        pass

    return {
        "total_targets": target_count,
        "total_drugs": drug_count,
        "approved_drugs": approved_drugs,
        "total_indications": indication_count,
        "target_families": families,
        "total_editing_assets": editing_count
    }


# ============ Editing Assets Pydantic Models ============

class EditingAssetSummary(BaseModel):
    id: str
    name: str
    sponsor: Optional[str] = None
    delivery_type: Optional[str] = None
    dbd_type: Optional[str] = None
    effector_type: Optional[str] = None
    effector_domains: Optional[List[str]] = None
    target_gene_symbol: Optional[str] = None
    primary_indication: Optional[str] = None
    phase: int = 0
    status: str = "unknown"
    total_editing_score: Optional[float] = None
    target_bio_score: Optional[float] = None
    modality_score: Optional[float] = None
    durability_score: Optional[float] = None


class EditingAssetDetail(BaseModel):
    id: str
    name: str
    sponsor: Optional[str] = None
    modality: str = "epigenetic_editor"
    delivery_type: Optional[str] = None
    dbd_type: Optional[str] = None
    effector_type: Optional[str] = None
    effector_domains: Optional[List[str]] = None
    target_gene_symbol: Optional[str] = None
    target_locus_description: Optional[str] = None
    primary_indication: Optional[str] = None
    phase: int = 0
    status: str = "unknown"
    mechanism_summary: Optional[str] = None
    description: Optional[str] = None
    source_url: Optional[str] = None


class EditingTargetGeneSummary(BaseModel):
    id: str
    symbol: str
    full_name: Optional[str] = None
    gene_category: Optional[str] = None
    is_classic_epi_target: bool = False
    editor_ready_status: str = "unknown"
    editing_program_count: int = 0


# ============ Editing Assets Endpoints ============

@router.get("/editing-assets", response_model=List[EditingAssetSummary])
async def list_editing_assets(
    sponsor: Optional[str] = None,
    dbd_type: Optional[str] = None,
    effector_type: Optional[str] = None,
    status: Optional[str] = None,
    min_phase: Optional[int] = None
):
    """List all epigenetic editing assets with optional filtering."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        query = supabase.table("epi_editing_assets").select("*")

        if sponsor:
            query = query.eq("sponsor", sponsor)
        if dbd_type:
            query = query.eq("dbd_type", dbd_type)
        if effector_type:
            query = query.eq("effector_type", effector_type)
        if status:
            query = query.eq("status", status)
        if min_phase is not None:
            query = query.gte("phase", min_phase)

        assets = query.execute().data

        result = []
        for asset in assets:
            # Get scores
            scores = supabase.table("epi_editing_scores")\
                .select("*")\
                .eq("editing_asset_id", asset["id"]).execute().data

            total_score = None
            bio_score = None
            modality_score = None
            durability_score = None

            if scores:
                s = scores[0]
                total_score = s.get("total_editing_score")
                bio_score = s.get("target_bio_score")
                modality_score = s.get("editing_modality_score")
                durability_score = s.get("durability_score")

            result.append(EditingAssetSummary(
                id=asset["id"],
                name=asset["name"],
                sponsor=asset.get("sponsor"),
                delivery_type=asset.get("delivery_type"),
                dbd_type=asset.get("dbd_type"),
                effector_type=asset.get("effector_type"),
                effector_domains=asset.get("effector_domains"),
                target_gene_symbol=asset.get("target_gene_symbol"),
                primary_indication=asset.get("primary_indication"),
                phase=asset.get("phase") or 0,
                status=asset.get("status") or "unknown",
                total_editing_score=round(total_score, 1) if total_score else None,
                target_bio_score=round(bio_score, 1) if bio_score else None,
                modality_score=round(modality_score, 1) if modality_score else None,
                durability_score=round(durability_score, 1) if durability_score else None
            ))

        # Sort by total_editing_score descending
        result.sort(key=lambda x: x.total_editing_score or 0, reverse=True)
        return result

    except Exception as e:
        # Table may not exist yet
        raise HTTPException(status_code=500, detail=f"Error fetching editing assets: {str(e)}")


@router.get("/editing-assets/{asset_id}")
async def get_editing_asset(asset_id: str):
    """Get detailed editing asset information with scores."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        # Get asset
        asset_result = supabase.table("epi_editing_assets")\
            .select("*")\
            .eq("id", asset_id)\
            .single().execute()

        if not asset_result.data:
            raise HTTPException(status_code=404, detail="Editing asset not found")

        asset = asset_result.data

        # Get scores
        scores = supabase.table("epi_editing_scores")\
            .select("*")\
            .eq("editing_asset_id", asset_id).execute().data

        # Get linked target genes
        target_links = supabase.table("epi_editing_asset_targets")\
            .select("*, epi_editing_target_genes(*)")\
            .eq("editing_asset_id", asset_id).execute().data

        return {
            "asset": EditingAssetDetail(
                id=asset["id"],
                name=asset["name"],
                sponsor=asset.get("sponsor"),
                modality=asset.get("modality") or "epigenetic_editor",
                delivery_type=asset.get("delivery_type"),
                dbd_type=asset.get("dbd_type"),
                effector_type=asset.get("effector_type"),
                effector_domains=asset.get("effector_domains"),
                target_gene_symbol=asset.get("target_gene_symbol"),
                target_locus_description=asset.get("target_locus_description"),
                primary_indication=asset.get("primary_indication"),
                phase=asset.get("phase") or 0,
                status=asset.get("status") or "unknown",
                mechanism_summary=asset.get("mechanism_summary"),
                description=asset.get("description"),
                source_url=asset.get("source_url")
            ),
            "scores": scores[0] if scores else None,
            "target_genes": target_links
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching editing asset: {str(e)}")


@router.get("/editing-targets", response_model=List[EditingTargetGeneSummary])
async def list_editing_targets(
    category: Optional[str] = None,
    editor_ready_only: bool = False
):
    """List all editing target genes with optional filtering."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        query = supabase.table("epi_editing_target_genes").select("*")

        if category:
            query = query.eq("gene_category", category)
        if editor_ready_only:
            query = query.neq("editor_ready_status", "unknown")

        genes = query.execute().data

        result = []
        for gene in genes:
            # Count editing programs targeting this gene
            program_count = len(supabase.table("epi_editing_asset_targets")\
                .select("editing_asset_id")\
                .eq("target_gene_id", gene["id"]).execute().data)

            result.append(EditingTargetGeneSummary(
                id=gene["id"],
                symbol=gene["symbol"],
                full_name=gene.get("full_name"),
                gene_category=gene.get("gene_category"),
                is_classic_epi_target=gene.get("is_classic_epi_target", False),
                editor_ready_status=gene.get("editor_ready_status", "unknown"),
                editing_program_count=program_count
            ))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching editing targets: {str(e)}")


@router.get("/editing-targets/{symbol}")
async def get_editing_target(symbol: str):
    """Get editing target gene details with editing programs."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        # Get target gene
        gene_result = supabase.table("epi_editing_target_genes")\
            .select("*")\
            .eq("symbol", symbol)\
            .single().execute()

        if not gene_result.data:
            raise HTTPException(status_code=404, detail="Editing target gene not found")

        gene = gene_result.data

        # Get editing programs
        programs = supabase.table("epi_editing_asset_targets")\
            .select("*, epi_editing_assets(*)")\
            .eq("target_gene_id", gene["id"]).execute().data

        # Get classic epi target link if exists
        epi_target = None
        if gene.get("epi_target_id"):
            epi_target_result = supabase.table("epi_targets")\
                .select("*")\
                .eq("id", gene["epi_target_id"]).execute()
            if epi_target_result.data:
                epi_target = epi_target_result.data[0]

        return {
            "target_gene": gene,
            "editing_programs": programs,
            "epi_target": epi_target
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching editing target: {str(e)}")


# ============ Company Pydantic Models ============

class CompanySummary(BaseModel):
    id: str
    name: str
    ticker: Optional[str] = None
    exchange: Optional[str] = None
    market_cap: Optional[int] = None
    epi_focus_score: Optional[float] = None
    is_pure_play_epi: bool = False
    drug_count: int = 0
    editing_asset_count: int = 0
    avg_drug_score: Optional[float] = None


class CompanyDetail(BaseModel):
    id: str
    name: str
    ticker: Optional[str] = None
    exchange: Optional[str] = None
    market_cap: Optional[int] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    headquarters: Optional[str] = None
    founded_year: Optional[int] = None
    employee_count: Optional[int] = None
    epi_focus_score: Optional[float] = None
    is_pure_play_epi: bool = False


# ============ Companies Endpoints ============

@router.get("/companies", response_model=List[CompanySummary])
async def list_companies(
    pure_play_only: bool = False,
    min_epi_focus: Optional[float] = None,
    has_ticker: Optional[bool] = None
):
    """List all companies with pipeline summaries."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        query = supabase.table("epi_companies").select("*")

        if pure_play_only:
            query = query.eq("is_pure_play_epi", True)
        if min_epi_focus:
            query = query.gte("epi_focus_score", min_epi_focus)
        if has_ticker is True:
            query = query.neq("ticker", None)

        companies = query.order("epi_focus_score", desc=True).execute().data

        result = []
        for c in companies:
            # Count drugs
            drug_links = supabase.table("epi_drug_companies")\
                .select("drug_id")\
                .eq("company_id", c["id"]).execute().data
            drug_count = len(drug_links)

            # Count editing assets
            editing_links = supabase.table("epi_editing_asset_companies")\
                .select("editing_asset_id")\
                .eq("company_id", c["id"]).execute().data
            editing_count = len(editing_links)

            # Get average drug score
            avg_score = None
            if drug_links:
                drug_ids = [d["drug_id"] for d in drug_links]
                scores = supabase.table("epi_scores")\
                    .select("total_score")\
                    .in_("drug_id", drug_ids).execute().data
                valid_scores = [s["total_score"] for s in scores if s.get("total_score")]
                if valid_scores:
                    avg_score = sum(valid_scores) / len(valid_scores)

            result.append(CompanySummary(
                id=c["id"],
                name=c["name"],
                ticker=c.get("ticker"),
                exchange=c.get("exchange"),
                market_cap=c.get("market_cap"),
                epi_focus_score=c.get("epi_focus_score"),
                is_pure_play_epi=c.get("is_pure_play_epi", False),
                drug_count=drug_count,
                editing_asset_count=editing_count,
                avg_drug_score=round(avg_score, 1) if avg_score else None
            ))

        # Sort by total asset count descending
        result.sort(key=lambda x: x.drug_count + x.editing_asset_count, reverse=True)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching companies: {str(e)}")


@router.get("/companies/{company_id}")
async def get_company(company_id: str):
    """Get company details with full pipeline."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        # Get company
        company_result = supabase.table("epi_companies")\
            .select("*")\
            .eq("id", company_id)\
            .single().execute()

        if not company_result.data:
            raise HTTPException(status_code=404, detail="Company not found")

        company = company_result.data

        # Get drugs with scores
        drug_links = supabase.table("epi_drug_companies")\
            .select("*, epi_drugs(*)")\
            .eq("company_id", company_id).execute().data

        drugs_with_scores = []
        for link in drug_links:
            drug = link.get("epi_drugs")
            if drug:
                # Get score
                scores = supabase.table("epi_scores")\
                    .select("*")\
                    .eq("drug_id", drug["id"]).execute().data
                score = scores[0] if scores else None
                drugs_with_scores.append({
                    "drug": drug,
                    "role": link.get("role"),
                    "is_primary": link.get("is_primary"),
                    "score": score
                })

        # Get editing assets with scores
        editing_links = supabase.table("epi_editing_asset_companies")\
            .select("*, epi_editing_assets(*)")\
            .eq("company_id", company_id).execute().data

        editing_with_scores = []
        for link in editing_links:
            asset = link.get("epi_editing_assets")
            if asset:
                scores = supabase.table("epi_editing_scores")\
                    .select("*")\
                    .eq("editing_asset_id", asset["id"]).execute().data
                score = scores[0] if scores else None
                editing_with_scores.append({
                    "asset": asset,
                    "role": link.get("role"),
                    "is_primary": link.get("is_primary"),
                    "score": score
                })

        return {
            "company": CompanyDetail(
                id=company["id"],
                name=company["name"],
                ticker=company.get("ticker"),
                exchange=company.get("exchange"),
                market_cap=company.get("market_cap"),
                sector=company.get("sector"),
                industry=company.get("industry"),
                description=company.get("description"),
                website=company.get("website"),
                headquarters=company.get("headquarters"),
                founded_year=company.get("founded_year"),
                employee_count=company.get("employee_count"),
                epi_focus_score=company.get("epi_focus_score"),
                is_pure_play_epi=company.get("is_pure_play_epi", False)
            ),
            "drugs": drugs_with_scores,
            "editing_assets": editing_with_scores
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching company: {str(e)}")


@router.get("/companies/ticker/{ticker}")
async def get_company_by_ticker(ticker: str):
    """Get company by stock ticker."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        company_result = supabase.table("epi_companies")\
            .select("*")\
            .eq("ticker", ticker.upper())\
            .single().execute()

        if not company_result.data:
            raise HTTPException(status_code=404, detail=f"Company with ticker {ticker} not found")

        # Redirect to full company endpoint
        return await get_company(company_result.data["id"])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching company: {str(e)}")


# ============ Patents Pydantic Models ============

class PatentSummary(BaseModel):
    id: str
    patent_number: str
    title: str
    assignee: Optional[str] = None
    pub_date: Optional[str] = None
    category: Optional[str] = None
    related_target_symbols: Optional[List[str]] = None


class PatentDetail(BaseModel):
    id: str
    patent_number: str
    title: str
    assignee: Optional[str] = None
    first_inventor: Optional[str] = None
    pub_date: Optional[str] = None
    category: Optional[str] = None
    abstract_snippet: Optional[str] = None
    related_target_symbols: Optional[List[str]] = None
    source_url: Optional[str] = None


# ============ Patents Endpoints ============

@router.get("/patents", response_model=List[PatentSummary])
async def list_patents(
    category: Optional[str] = None,
    assignee: Optional[str] = None,
    target_symbol: Optional[str] = None,
    limit: int = Query(default=50, le=200)
):
    """List epigenetic patents with optional filtering."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        query = supabase.table("epi_patents").select("*")

        if category:
            query = query.eq("category", category)
        if assignee:
            query = query.ilike("assignee", f"%{assignee}%")
        if target_symbol:
            query = query.contains("related_target_symbols", [target_symbol])

        patents = query.order("pub_date", desc=True).limit(limit).execute().data

        return [
            PatentSummary(
                id=p["id"],
                patent_number=p["patent_number"],
                title=p["title"],
                assignee=p.get("assignee"),
                pub_date=str(p["pub_date"]) if p.get("pub_date") else None,
                category=p.get("category"),
                related_target_symbols=p.get("related_target_symbols")
            )
            for p in patents
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching patents: {str(e)}")


@router.get("/patents/{patent_id}")
async def get_patent(patent_id: str):
    """Get patent details."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        result = supabase.table("epi_patents")\
            .select("*")\
            .eq("id", patent_id)\
            .single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Patent not found")

        p = result.data
        return PatentDetail(
            id=p["id"],
            patent_number=p["patent_number"],
            title=p["title"],
            assignee=p.get("assignee"),
            first_inventor=p.get("first_inventor"),
            pub_date=str(p["pub_date"]) if p.get("pub_date") else None,
            category=p.get("category"),
            abstract_snippet=p.get("abstract_snippet"),
            related_target_symbols=p.get("related_target_symbols"),
            source_url=p.get("source_url")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching patent: {str(e)}")


# ============ News Pydantic Models ============

class NewsSummary(BaseModel):
    id: str
    title: str
    source: Optional[str] = None
    pub_date: Optional[str] = None
    category: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_impact_flag: Optional[str] = None


class NewsDetail(BaseModel):
    id: str
    title: str
    source: Optional[str] = None
    url: Optional[str] = None
    pub_date: Optional[str] = None
    category: Optional[str] = None
    raw_text: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_impact_flag: Optional[str] = None
    ai_extracted_entities: Optional[dict] = None
    related_drug_ids: Optional[List[str]] = None
    related_target_ids: Optional[List[str]] = None
    related_editing_asset_ids: Optional[List[str]] = None


# ============ News Endpoints ============

@router.get("/news", response_model=List[NewsSummary])
async def list_news(
    category: Optional[str] = None,
    source: Optional[str] = None,
    impact_flag: Optional[str] = None,
    limit: int = Query(default=50, le=200)
):
    """List AI-analyzed news and research articles."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        query = supabase.table("epi_news").select("*")

        if category:
            query = query.eq("category", category)
        if source:
            query = query.ilike("source", f"%{source}%")
        if impact_flag:
            query = query.eq("ai_impact_flag", impact_flag)

        news = query.order("pub_date", desc=True).limit(limit).execute().data

        return [
            NewsSummary(
                id=n["id"],
                title=n["title"],
                source=n.get("source"),
                pub_date=str(n["pub_date"]) if n.get("pub_date") else None,
                category=n.get("category"),
                ai_summary=n.get("ai_summary"),
                ai_impact_flag=n.get("ai_impact_flag")
            )
            for n in news
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")


@router.get("/news/{news_id}")
async def get_news(news_id: str):
    """Get news article details with AI analysis."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        result = supabase.table("epi_news")\
            .select("*")\
            .eq("id", news_id)\
            .single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="News article not found")

        n = result.data
        return NewsDetail(
            id=n["id"],
            title=n["title"],
            source=n.get("source"),
            url=n.get("url"),
            pub_date=str(n["pub_date"]) if n.get("pub_date") else None,
            category=n.get("category"),
            raw_text=n.get("raw_text"),
            ai_summary=n.get("ai_summary"),
            ai_impact_flag=n.get("ai_impact_flag"),
            ai_extracted_entities=n.get("ai_extracted_entities"),
            related_drug_ids=n.get("related_drug_ids"),
            related_target_ids=n.get("related_target_ids"),
            related_editing_asset_ids=n.get("related_editing_asset_ids")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")


# ============ Enhanced Target Endpoint (with new annotations) ============

# ============ Combos Pydantic Models ============

class ComboSummary(BaseModel):
    id: str
    combo_label: str  # 'epi+IO', 'epi+KRAS', 'epi+radiation', etc.
    epi_drug_id: str
    epi_drug_name: str
    partner_class: Optional[str] = None
    partner_drug_name: Optional[str] = None
    indication_id: str
    indication_name: str
    max_phase: Optional[int] = None
    nct_id: Optional[str] = None
    source: Optional[str] = None


class ComboDetail(BaseModel):
    id: str
    combo_label: str
    epi_drug_id: str
    epi_drug_name: str
    epi_drug_chembl_id: Optional[str] = None
    partner_drug_id: Optional[str] = None
    partner_class: Optional[str] = None
    partner_drug_name: Optional[str] = None
    indication_id: str
    indication_name: str
    indication_efo_id: Optional[str] = None
    max_phase: Optional[int] = None
    nct_id: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    notes: Optional[str] = None


# ============ Combos Endpoints ============

@router.get("/combos", response_model=List[ComboSummary])
async def list_combos(
    combo_label: Optional[str] = None,
    epi_drug_id: Optional[str] = None,
    indication_id: Optional[str] = None,
    partner_class: Optional[str] = None,
    min_phase: Optional[int] = None
):
    """
    List combination therapies involving epigenetic drugs.

    Combo labels:
    - epi+IO: Epigenetic + checkpoint inhibitor
    - epi+KRAS: Epigenetic + KRAS inhibitor
    - epi+radiation: Epigenetic + radiotherapy
    - epi+Venetoclax: Epigenetic + BCL2 inhibitor
    - epi+chemotherapy: Epigenetic + chemotherapy
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        query = supabase.table("epi_combos").select(
            "*, epi_drugs!epi_combos_epi_drug_id_fkey(name, chembl_id), epi_indications(name, efo_id)"
        )

        if combo_label:
            query = query.eq("combo_label", combo_label)
        if epi_drug_id:
            query = query.eq("epi_drug_id", epi_drug_id)
        if indication_id:
            query = query.eq("indication_id", indication_id)
        if partner_class:
            query = query.eq("partner_class", partner_class)
        if min_phase is not None:
            query = query.gte("max_phase", min_phase)

        combos = query.order("max_phase", desc=True).execute().data

        return [
            ComboSummary(
                id=c["id"],
                combo_label=c["combo_label"],
                epi_drug_id=c["epi_drug_id"],
                epi_drug_name=c["epi_drugs"]["name"] if c.get("epi_drugs") else "Unknown",
                partner_class=c.get("partner_class"),
                partner_drug_name=c.get("partner_drug_name"),
                indication_id=c["indication_id"],
                indication_name=c["epi_indications"]["name"] if c.get("epi_indications") else "Unknown",
                max_phase=c.get("max_phase"),
                nct_id=c.get("nct_id"),
                source=c.get("source")
            )
            for c in combos
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching combos: {str(e)}")


@router.get("/combos/labels")
async def get_combo_labels():
    """Get all combo labels with counts."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        combos = supabase.table("epi_combos").select("combo_label").execute().data

        label_counts = {}
        for c in combos:
            label = c["combo_label"]
            label_counts[label] = label_counts.get(label, 0) + 1

        return {
            "labels": [
                {"label": label, "count": count}
                for label, count in sorted(label_counts.items(), key=lambda x: -x[1])
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching combo labels: {str(e)}")


@router.get("/combos/{combo_id}")
async def get_combo(combo_id: str):
    """Get detailed combo information."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        combo_result = supabase.table("epi_combos")\
            .select("*, epi_drugs!epi_combos_epi_drug_id_fkey(*), epi_indications(*)")\
            .eq("id", combo_id)\
            .single().execute()

        if not combo_result.data:
            raise HTTPException(status_code=404, detail="Combo not found")

        c = combo_result.data
        drug = c.get("epi_drugs", {})
        indication = c.get("epi_indications", {})

        # Get partner drug details if partner_drug_id exists
        partner_drug = None
        if c.get("partner_drug_id"):
            partner_result = supabase.table("epi_drugs")\
                .select("*")\
                .eq("id", c["partner_drug_id"])\
                .single().execute()
            partner_drug = partner_result.data

        return {
            "combo": ComboDetail(
                id=c["id"],
                combo_label=c["combo_label"],
                epi_drug_id=c["epi_drug_id"],
                epi_drug_name=drug.get("name", "Unknown"),
                epi_drug_chembl_id=drug.get("chembl_id"),
                partner_drug_id=c.get("partner_drug_id"),
                partner_class=c.get("partner_class"),
                partner_drug_name=c.get("partner_drug_name"),
                indication_id=c["indication_id"],
                indication_name=indication.get("name", "Unknown"),
                indication_efo_id=indication.get("efo_id"),
                max_phase=c.get("max_phase"),
                nct_id=c.get("nct_id"),
                source=c.get("source"),
                source_url=c.get("source_url"),
                notes=c.get("notes")
            ),
            "epi_drug": drug,
            "partner_drug": partner_drug,
            "indication": indication
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching combo: {str(e)}")


@router.get("/drugs/{drug_id}/combos", response_model=List[ComboSummary])
async def get_drug_combos(drug_id: str):
    """Get all combinations involving a specific epigenetic drug."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        combos = supabase.table("epi_combos")\
            .select("*, epi_drugs!epi_combos_epi_drug_id_fkey(name), epi_indications(name)")\
            .eq("epi_drug_id", drug_id)\
            .order("max_phase", desc=True)\
            .execute().data

        return [
            ComboSummary(
                id=c["id"],
                combo_label=c["combo_label"],
                epi_drug_id=c["epi_drug_id"],
                epi_drug_name=c["epi_drugs"]["name"] if c.get("epi_drugs") else "Unknown",
                partner_class=c.get("partner_class"),
                partner_drug_name=c.get("partner_drug_name"),
                indication_id=c["indication_id"],
                indication_name=c["epi_indications"]["name"] if c.get("epi_indications") else "Unknown",
                max_phase=c.get("max_phase"),
                nct_id=c.get("nct_id"),
                source=c.get("source")
            )
            for c in combos
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching drug combos: {str(e)}")


# ============ Per-Target Activity Endpoints ============

class TargetActivitySummary(BaseModel):
    target_chembl_id: str
    target_name: str
    target_type: Optional[str] = None
    best_pact: Optional[float] = None
    median_pact: Optional[float] = None
    best_value_nm: Optional[float] = None
    n_activities: int = 0
    activity_types: Optional[List[str]] = None
    is_primary_target: bool = False


@router.get("/drugs/{drug_id}/target-activities", response_model=List[TargetActivitySummary])
async def get_drug_target_activities(drug_id: str):
    """
    Get per-target activity breakdown for a drug.
    Returns potency data by target, sorted from highest to lowest pXC50.

    Use this for potency visualization showing selectivity across targets.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        activities = supabase.table("chembl_target_activities")\
            .select("*")\
            .eq("drug_id", drug_id)\
            .order("best_pact", desc=True)\
            .execute().data

        return [
            TargetActivitySummary(
                target_chembl_id=a["target_chembl_id"],
                target_name=a["target_name"],
                target_type=a.get("target_type"),
                best_pact=round(a["best_pact"], 2) if a.get("best_pact") else None,
                median_pact=round(a["median_pact"], 2) if a.get("median_pact") else None,
                best_value_nm=round(a["best_value_nm"], 2) if a.get("best_value_nm") else None,
                n_activities=a.get("n_activities", 0),
                activity_types=a.get("activity_types"),
                is_primary_target=a.get("is_primary_target", False)
            )
            for a in activities
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching target activities: {str(e)}")


@router.get("/targets/{target_id}/enriched")
async def get_target_enriched(target_id: str):
    """Get target with IO exhaustion, resistance, and aging annotations plus related entities."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        # Get target with new annotations
        target_result = supabase.table("epi_targets")\
            .select("*")\
            .eq("id", target_id)\
            .single().execute()

        if not target_result.data:
            raise HTTPException(status_code=404, detail="Target not found")

        target = target_result.data

        # Get related drugs
        drug_links = supabase.table("epi_drug_targets")\
            .select("*, epi_drugs(*)")\
            .eq("target_id", target_id).execute().data

        drugs = []
        for link in drug_links:
            drug = link.get("epi_drugs")
            if drug:
                # Get score
                scores = supabase.table("epi_scores")\
                    .select("total_score")\
                    .eq("drug_id", drug["id"]).execute().data
                best_score = max([s["total_score"] for s in scores if s.get("total_score")], default=None)
                drugs.append({
                    "id": drug["id"],
                    "name": drug["name"],
                    "mechanism": link.get("mechanism_of_action"),
                    "total_score": best_score
                })

        # Get related editing assets
        editing_assets = supabase.table("epi_editing_assets")\
            .select("id, name, sponsor, status")\
            .or_(f"target_gene_id.eq.{target_id},target_gene_symbol.eq.{target['symbol']}")\
            .execute().data

        # Get related patents
        patents = supabase.table("epi_patents")\
            .select("id, patent_number, title, category")\
            .contains("related_target_symbols", [target["symbol"]])\
            .execute().data

        return {
            "target": {
                **target,
                "io_exhaustion_axis": target.get("io_exhaustion_axis", False),
                "epi_resistance_role": target.get("epi_resistance_role"),
                "aging_clock_relevance": target.get("aging_clock_relevance"),
            },
            "drugs": drugs,
            "editing_assets": editing_assets,
            "patents": patents
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching enriched target: {str(e)}")
