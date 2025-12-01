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
    has_api_key = bool(os.getenv("GEMINI_API_KEY"))

    return {
        "status": "ready" if has_api_key else "no_api_key",
        "gemini_configured": has_api_key,
        "message": "AI endpoints ready" if has_api_key else "Set GEMINI_API_KEY to enable AI features"
    }
