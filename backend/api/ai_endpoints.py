"""
AI Endpoints - FastAPI routes for AI chat and explanations.

Endpoints:
- POST /ai/chat - General chat with epigenetics assistant
- POST /ai/explain-scorecard - Explain a drug-indication scorecard
- POST /ai/explain-editing-asset - Explain an epigenetic editing asset
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.ai.client import get_ai_client
from backend.ai.context_builder import ContextBuilder
from backend.ai.prompts import SYSTEM_PROMPTS

router = APIRouter(prefix="/ai", tags=["AI Chat"])

# Initialize context builder
context_builder = ContextBuilder()


# =========================================================================
# Request/Response Models
# =========================================================================

class ChatMessage(BaseModel):
    """A single chat message."""
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Request for general chat."""
    question: str
    entity_refs: Optional[Dict[str, List[str]]] = None
    conversation_history: Optional[List[ChatMessage]] = None
    temperature: float = 0.7


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    answer: str
    entities_found: Dict[str, List[str]]
    model_used: str


class ScorecardRequest(BaseModel):
    """Request to explain a scorecard."""
    drug_id: str
    indication_id: str
    temperature: float = 0.5


class ScorecardResponse(BaseModel):
    """Response from scorecard explanation."""
    explanation: str
    drug_name: str
    indication_name: str
    scores: Optional[Dict[str, Any]]
    model_used: str


class EditingAssetRequest(BaseModel):
    """Request to explain an editing asset."""
    asset_id: str
    temperature: float = 0.5


class EditingAssetResponse(BaseModel):
    """Response from editing asset explanation."""
    explanation: str
    asset_name: str
    target_symbol: Optional[str]
    scores: Optional[Dict[str, Any]]
    model_used: str


# =========================================================================
# Endpoints
# =========================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    General chat endpoint for epigenetics questions.

    The AI will:
    1. Extract entity references from the question
    2. Retrieve relevant context from the database
    3. Generate a grounded response using Gemini

    Example questions:
    - "What is Vorinostat used for?"
    - "Compare HDAC inhibitors to BET inhibitors"
    - "List all Phase 3 epigenetic drugs"
    """
    ai_client = get_ai_client()

    # Extract entities from question
    if request.entity_refs:
        entities = request.entity_refs
    else:
        entities = context_builder.extract_entities_from_question(request.question)

    # Build context from database
    context = context_builder.build_chat_context(request.question, entities)

    # Generate response
    if request.conversation_history:
        # Multi-turn conversation
        messages = [{"role": m.role, "content": m.content} for m in request.conversation_history]
        messages.append({"role": "user", "content": request.question})

        answer = ai_client.generate_with_history(
            messages=messages,
            system_prompt=SYSTEM_PROMPTS["chat"],
            context=context,
            temperature=request.temperature
        )
    else:
        # Single question
        answer = ai_client.generate(
            prompt=request.question,
            system_prompt=SYSTEM_PROMPTS["chat"],
            context=context,
            temperature=request.temperature
        )

    return ChatResponse(
        answer=answer,
        entities_found=entities,
        model_used=ai_client.model_name if hasattr(ai_client, 'model_name') else "mock"
    )


@router.post("/explain-scorecard", response_model=ScorecardResponse)
async def explain_scorecard(request: ScorecardRequest):
    """
    Explain why a drug has its current scores for an indication.

    Provides detailed breakdown of:
    - BioScore: Biological rationale
    - ChemScore: Chemistry quality
    - TractabilityScore: Target druggability
    - TotalScore: Overall assessment
    """
    ai_client = get_ai_client()

    # Get scorecard context
    context = context_builder.get_scorecard_context(
        drug_id=request.drug_id,
        indication_id=request.indication_id
    )

    if not context:
        raise HTTPException(
            status_code=404,
            detail=f"Scorecard not found for drug_id={request.drug_id}, indication_id={request.indication_id}"
        )

    drug_name = context["drug"]["name"]
    indication_name = context["indication"]["name"]

    # Generate explanation
    prompt = f"Explain the scorecard for {drug_name} in {indication_name}."

    explanation = ai_client.generate(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPTS["scorecard"],
        context=context,
        temperature=request.temperature
    )

    return ScorecardResponse(
        explanation=explanation,
        drug_name=drug_name,
        indication_name=indication_name,
        scores=context.get("scores"),
        model_used=ai_client.model_name if hasattr(ai_client, 'model_name') else "mock"
    )


@router.post("/explain-editing-asset", response_model=EditingAssetResponse)
async def explain_editing_asset(request: EditingAssetRequest):
    """
    Explain an epigenetic editing asset.

    Provides breakdown of:
    - Technology: DBD type, effector domains, delivery
    - Target: Gene being silenced and rationale
    - Comparison: vs small molecule approaches
    - Scores: Modality, durability, bio scores
    """
    ai_client = get_ai_client()

    # Get editing asset context
    context = context_builder.get_editing_asset_context(asset_id=request.asset_id)

    if not context:
        raise HTTPException(
            status_code=404,
            detail=f"Editing asset not found: {request.asset_id}"
        )

    asset = context["editing_asset"]
    asset_name = asset["name"]
    target_symbol = asset.get("target_gene_symbol")

    # Generate explanation
    prompt = f"Explain the epigenetic editing asset {asset_name}."

    explanation = ai_client.generate(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPTS["editing_asset"],
        context=context,
        temperature=request.temperature
    )

    return EditingAssetResponse(
        explanation=explanation,
        asset_name=asset_name,
        target_symbol=target_symbol,
        scores=context.get("scores"),
        model_used=ai_client.model_name if hasattr(ai_client, 'model_name') else "mock"
    )


# =========================================================================
# Utility Endpoints
# =========================================================================

@router.get("/entities")
async def list_known_entities():
    """
    List all known entities in the database that the AI can discuss.

    Useful for autocomplete or showing available options.
    """
    from backend.etl.supabase_client import supabase

    drugs = supabase.table('epi_drugs').select('id, name').execute().data
    targets = supabase.table('epi_targets').select('id, symbol, name, family').execute().data
    indications = supabase.table('epi_indications').select('id, name').execute().data
    editing = supabase.table('epi_editing_assets').select('id, name, sponsor').execute().data

    return {
        "drugs": [{"id": d["id"], "name": d["name"]} for d in drugs],
        "targets": [{"id": t["id"], "symbol": t["symbol"], "name": t.get("name"), "family": t.get("family")} for t in targets],
        "indications": [{"id": i["id"], "name": i["name"]} for i in indications],
        "editing_assets": [{"id": e["id"], "name": e["name"], "sponsor": e.get("sponsor")} for e in editing]
    }


@router.get("/health")
async def ai_health():
    """Check if AI service is configured and ready."""
    import os
    has_gemini = bool(os.getenv("GEMINI_API_KEY"))
    has_perplexity = bool(os.getenv("PERPLEXITY_API_KEY"))

    return {
        "status": "ready" if has_gemini else "no_api_key",
        "gemini_configured": has_gemini,
        "perplexity_configured": has_perplexity,
        "message": "AI endpoints ready" if has_gemini else "Set GEMINI_API_KEY to enable AI features"
    }


# =========================================================================
# Fact-Check Endpoints (Perplexity)
# =========================================================================

class FactCheckDrugRequest(BaseModel):
    """Request to fact-check a drug."""
    drug_id: str


class FactCheckTargetRequest(BaseModel):
    """Request to fact-check a target."""
    target_id: str


class FactCheckResponse(BaseModel):
    """Response from fact-check endpoint."""
    entity_name: str
    entity_type: str
    our_data: dict
    verified_data: Optional[dict] = None
    discrepancies: list
    has_discrepancies: bool
    citations: Optional[list] = None
    error: Optional[str] = None
    checked_at: str


@router.post("/fact-check/drug", response_model=FactCheckResponse)
async def fact_check_drug(request: FactCheckDrugRequest):
    """
    Fact-check a drug record using Perplexity API.

    Verifies:
    - Current developer/owner company
    - Clinical trial phase
    - Approved/investigated indications
    - Primary target

    Returns discrepancies for admin review.
    """
    import os
    from backend.etl.supabase_client import supabase

    if not os.getenv("PERPLEXITY_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="PERPLEXITY_API_KEY not configured. Set it to enable fact-checking."
        )

    # Get drug from database
    drug_result = supabase.table('epi_drugs').select('*').eq('id', request.drug_id).single().execute()

    if not drug_result.data:
        raise HTTPException(status_code=404, detail=f"Drug not found: {request.drug_id}")

    drug = drug_result.data

    # Get associated targets
    targets = supabase.table('epi_drug_targets').select('target_id, epi_targets(symbol)').eq('drug_id', request.drug_id).execute().data
    target_symbols = [t['epi_targets']['symbol'] for t in targets if t.get('epi_targets')]

    # Get associated indications
    indications = supabase.table('epi_drug_indications').select('indication_id, epi_indications(name)').eq('drug_id', request.drug_id).execute().data
    indication_names = [i['epi_indications']['name'] for i in indications if i.get('epi_indications')]

    # Build our data record
    our_data = {
        "company": drug.get("sponsor") or drug.get("source"),
        "phase": drug.get("max_phase"),
        "indications": indication_names,
        "target": target_symbols[0] if target_symbols else None,
        "chembl_id": drug.get("chembl_id")
    }

    # Call Perplexity
    from backend.ai.fact_check import FactCheckService
    service = FactCheckService()
    result = await service.verify_drug(drug["name"], our_data)

    # Log to fact_check_log table
    try:
        supabase.table('fact_check_log').insert({
            "entity_type": "drug",
            "entity_id": request.drug_id,
            "entity_name": drug["name"],
            "our_data": our_data,
            "perplexity_response": result.get("raw_response"),
            "perplexity_summary": result.get("verified_data", {}).get("recent_news"),
            "discrepancies": result.get("discrepancies"),
            "has_discrepancies": result.get("has_discrepancies", False),
            "status": "pending" if result.get("has_discrepancies") else "confirmed"
        }).execute()
    except Exception as e:
        print(f"Failed to log fact-check: {e}")

    return FactCheckResponse(
        entity_name=drug["name"],
        entity_type="drug",
        our_data=our_data,
        verified_data=result.get("verified_data"),
        discrepancies=result.get("discrepancies", []),
        has_discrepancies=result.get("has_discrepancies", False),
        citations=result.get("citations"),
        error=result.get("error"),
        checked_at=result.get("checked_at", "")
    )


@router.post("/fact-check/target", response_model=FactCheckResponse)
async def fact_check_target(request: FactCheckTargetRequest):
    """
    Fact-check a target record using Perplexity API.

    Verifies:
    - Gene/protein name and function
    - Target family classification
    - Known drugs targeting this protein
    """
    import os
    from backend.etl.supabase_client import supabase

    if not os.getenv("PERPLEXITY_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="PERPLEXITY_API_KEY not configured. Set it to enable fact-checking."
        )

    # Get target from database
    target_result = supabase.table('epi_targets').select('*').eq('id', request.target_id).single().execute()

    if not target_result.data:
        raise HTTPException(status_code=404, detail=f"Target not found: {request.target_id}")

    target = target_result.data

    # Get associated drugs
    drugs = supabase.table('epi_drug_targets').select('drug_id, epi_drugs(name)').eq('target_id', request.target_id).execute().data
    drug_names = [d['epi_drugs']['name'] for d in drugs if d.get('epi_drugs')]

    our_data = {
        "name": target.get("name"),
        "family": target.get("family"),
        "class": target.get("class"),
        "drugs_in_development": drug_names
    }

    # Call Perplexity
    from backend.ai.fact_check import FactCheckService
    service = FactCheckService()
    result = await service.verify_target(target["symbol"], our_data)

    # Log to fact_check_log table
    try:
        supabase.table('fact_check_log').insert({
            "entity_type": "target",
            "entity_id": request.target_id,
            "entity_name": target["symbol"],
            "our_data": our_data,
            "perplexity_response": result.get("raw_response"),
            "discrepancies": result.get("discrepancies"),
            "has_discrepancies": result.get("has_discrepancies", False),
            "status": "pending" if result.get("has_discrepancies") else "confirmed"
        }).execute()
    except Exception as e:
        print(f"Failed to log fact-check: {e}")

    return FactCheckResponse(
        entity_name=target["symbol"],
        entity_type="target",
        our_data=our_data,
        verified_data=result.get("verified_data"),
        discrepancies=result.get("discrepancies", []),
        has_discrepancies=result.get("has_discrepancies", False),
        citations=result.get("citations"),
        error=result.get("error"),
        checked_at=result.get("checked_at", "")
    )
