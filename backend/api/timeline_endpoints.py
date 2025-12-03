"""
Timeline API Endpoints
Historical tracking of drug phases, company entries, and target activity
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
from datetime import date, datetime
from backend.etl.supabase_client import supabase

router = APIRouter(prefix="/timeline", tags=["Timeline"])


# ============================================
# Pydantic Models
# ============================================

class DrugPhaseEvent(BaseModel):
    id: str
    drug_id: str
    drug_name: str
    phase_from: Optional[int] = None
    phase_to: int
    fda_approved_from: bool = False
    fda_approved_to: bool = False
    indication_id: Optional[str] = None
    indication_name: Optional[str] = None
    source: Optional[str] = None
    change_date: str
    detected_at: str


class CompanyEntryEvent(BaseModel):
    id: str
    company_id: str
    company_name: str
    event_type: str
    event_description: Optional[str] = None
    drug_id: Optional[str] = None
    drug_name: Optional[str] = None
    target_id: Optional[str] = None
    target_symbol: Optional[str] = None
    source: Optional[str] = None
    event_date: str


class TargetActivityEvent(BaseModel):
    id: str
    target_id: str
    target_symbol: str
    event_type: str
    drug_id: Optional[str] = None
    drug_name: Optional[str] = None
    phase: Optional[int] = None
    source: Optional[str] = None
    event_date: str


class TimelineSummary(BaseModel):
    total_events: int
    drug_phase_changes: int
    company_entries: int
    target_activities: int
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None


# ============================================
# Drug Phase History Endpoints
# ============================================

@router.get("/drugs", response_model=List[DrugPhaseEvent])
async def list_drug_phase_events(
    drug_id: Optional[str] = None,
    phase: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    approvals_only: bool = False,
    limit: int = Query(default=100, le=500)
):
    """
    Get drug phase change history.

    - Filter by specific drug
    - Filter by phase (e.g., all Phase 3 entries)
    - Filter by date range
    - Option to show only FDA approvals
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        query = supabase.table("epi_drug_phase_history").select("*")

        if drug_id:
            query = query.eq("drug_id", drug_id)
        if phase is not None:
            query = query.eq("phase_to", phase)
        if start_date:
            query = query.gte("change_date", start_date)
        if end_date:
            query = query.lte("change_date", end_date)
        if approvals_only:
            query = query.eq("fda_approved_to", True).eq("fda_approved_from", False)

        result = query.order("change_date", desc=True).limit(limit).execute()

        return [
            DrugPhaseEvent(
                id=e["id"],
                drug_id=e["drug_id"],
                drug_name=e["drug_name"],
                phase_from=e.get("phase_from"),
                phase_to=e["phase_to"],
                fda_approved_from=e.get("fda_approved_from", False),
                fda_approved_to=e.get("fda_approved_to", False),
                indication_id=e.get("indication_id"),
                indication_name=e.get("indication_name"),
                source=e.get("source"),
                change_date=str(e["change_date"]),
                detected_at=str(e["detected_at"])
            )
            for e in (result.data or [])
        ]

    except Exception as e:
        # Table may not exist yet
        return []


@router.get("/drugs/{drug_id}/history", response_model=List[DrugPhaseEvent])
async def get_drug_history(drug_id: str):
    """
    Get complete phase history for a specific drug.

    Answers: "When did this drug enter Phase 3?"
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        result = supabase.table("epi_drug_phase_history")\
            .select("*")\
            .eq("drug_id", drug_id)\
            .order("change_date", desc=False)\
            .execute()

        return [
            DrugPhaseEvent(
                id=e["id"],
                drug_id=e["drug_id"],
                drug_name=e["drug_name"],
                phase_from=e.get("phase_from"),
                phase_to=e["phase_to"],
                fda_approved_from=e.get("fda_approved_from", False),
                fda_approved_to=e.get("fda_approved_to", False),
                indication_id=e.get("indication_id"),
                indication_name=e.get("indication_name"),
                source=e.get("source"),
                change_date=str(e["change_date"]),
                detected_at=str(e["detected_at"])
            )
            for e in (result.data or [])
        ]

    except Exception as e:
        return []


# ============================================
# Company Entry History Endpoints
# ============================================

@router.get("/companies", response_model=List[CompanyEntryEvent])
async def list_company_events(
    company_id: Optional[str] = None,
    event_type: Optional[str] = None,
    target_symbol: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(default=100, le=500)
):
    """
    Get company entry/activity history.

    Event types: 'first_drug', 'acquisition', 'partnership', 'ipo', 'bankruptcy'

    Answers: "When did Lilly enter the EZH2 space?"
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        query = supabase.table("epi_company_entry_history").select("*")

        if company_id:
            query = query.eq("company_id", company_id)
        if event_type:
            query = query.eq("event_type", event_type)
        if target_symbol:
            query = query.eq("target_symbol", target_symbol)
        if start_date:
            query = query.gte("event_date", start_date)
        if end_date:
            query = query.lte("event_date", end_date)

        result = query.order("event_date", desc=True).limit(limit).execute()

        return [
            CompanyEntryEvent(
                id=e["id"],
                company_id=e["company_id"],
                company_name=e["company_name"],
                event_type=e["event_type"],
                event_description=e.get("event_description"),
                drug_id=e.get("drug_id"),
                drug_name=e.get("drug_name"),
                target_id=e.get("target_id"),
                target_symbol=e.get("target_symbol"),
                source=e.get("source"),
                event_date=str(e["event_date"])
            )
            for e in (result.data or [])
        ]

    except Exception as e:
        return []


@router.get("/companies/{company_id}/history", response_model=List[CompanyEntryEvent])
async def get_company_history(company_id: str):
    """
    Get complete activity history for a specific company.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        result = supabase.table("epi_company_entry_history")\
            .select("*")\
            .eq("company_id", company_id)\
            .order("event_date", desc=False)\
            .execute()

        return [
            CompanyEntryEvent(
                id=e["id"],
                company_id=e["company_id"],
                company_name=e["company_name"],
                event_type=e["event_type"],
                event_description=e.get("event_description"),
                drug_id=e.get("drug_id"),
                drug_name=e.get("drug_name"),
                target_id=e.get("target_id"),
                target_symbol=e.get("target_symbol"),
                source=e.get("source"),
                event_date=str(e["event_date"])
            )
            for e in (result.data or [])
        ]

    except Exception as e:
        return []


# ============================================
# Target Activity History Endpoints
# ============================================

@router.get("/targets", response_model=List[TargetActivityEvent])
async def list_target_events(
    target_id: Optional[str] = None,
    target_symbol: Optional[str] = None,
    event_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(default=100, le=500)
):
    """
    Get target activity history.

    Event types: 'drug_added', 'drug_removed', 'approval', 'trial_started'
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        query = supabase.table("epi_target_activity_history").select("*")

        if target_id:
            query = query.eq("target_id", target_id)
        if target_symbol:
            query = query.eq("target_symbol", target_symbol)
        if event_type:
            query = query.eq("event_type", event_type)
        if start_date:
            query = query.gte("event_date", start_date)
        if end_date:
            query = query.lte("event_date", end_date)

        result = query.order("event_date", desc=True).limit(limit).execute()

        return [
            TargetActivityEvent(
                id=e["id"],
                target_id=e["target_id"],
                target_symbol=e["target_symbol"],
                event_type=e["event_type"],
                drug_id=e.get("drug_id"),
                drug_name=e.get("drug_name"),
                phase=e.get("phase"),
                source=e.get("source"),
                event_date=str(e["event_date"])
            )
            for e in (result.data or [])
        ]

    except Exception as e:
        return []


@router.get("/targets/{target_symbol}/history", response_model=List[TargetActivityEvent])
async def get_target_history(target_symbol: str):
    """
    Get complete activity history for a specific target.

    Answers: "When did companies start targeting HDAC1?"
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        result = supabase.table("epi_target_activity_history")\
            .select("*")\
            .eq("target_symbol", target_symbol.upper())\
            .order("event_date", desc=False)\
            .execute()

        return [
            TargetActivityEvent(
                id=e["id"],
                target_id=e["target_id"],
                target_symbol=e["target_symbol"],
                event_type=e["event_type"],
                drug_id=e.get("drug_id"),
                drug_name=e.get("drug_name"),
                phase=e.get("phase"),
                source=e.get("source"),
                event_date=str(e["event_date"])
            )
            for e in (result.data or [])
        ]

    except Exception as e:
        return []


# ============================================
# Timeline Summary
# ============================================

@router.get("/summary", response_model=TimelineSummary)
async def get_timeline_summary():
    """
    Get overall timeline statistics.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        drug_events = supabase.table("epi_drug_phase_history").select("id, change_date").execute()
        company_events = supabase.table("epi_company_entry_history").select("id, event_date").execute()
        target_events = supabase.table("epi_target_activity_history").select("id, event_date").execute()

        drug_count = len(drug_events.data or [])
        company_count = len(company_events.data or [])
        target_count = len(target_events.data or [])

        # Get date range
        all_dates = []
        for e in (drug_events.data or []):
            if e.get("change_date"):
                all_dates.append(str(e["change_date"]))
        for e in (company_events.data or []):
            if e.get("event_date"):
                all_dates.append(str(e["event_date"]))
        for e in (target_events.data or []):
            if e.get("event_date"):
                all_dates.append(str(e["event_date"]))

        start_date = min(all_dates) if all_dates else None
        end_date = max(all_dates) if all_dates else None

        return TimelineSummary(
            total_events=drug_count + company_count + target_count,
            drug_phase_changes=drug_count,
            company_entries=company_count,
            target_activities=target_count,
            date_range_start=start_date,
            date_range_end=end_date
        )

    except Exception as e:
        return TimelineSummary(
            total_events=0,
            drug_phase_changes=0,
            company_entries=0,
            target_activities=0
        )


# ============================================
# Recent Activity Feed
# ============================================

@router.get("/recent")
async def get_recent_activity(
    days: int = Query(default=30, le=365),
    limit: int = Query(default=50, le=200)
):
    """
    Get recent activity across all entity types.

    Returns a unified feed of recent events for the activity dashboard.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    from datetime import timedelta
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    events = []

    try:
        # Drug phase changes
        drug_events = supabase.table("epi_drug_phase_history")\
            .select("*")\
            .gte("change_date", cutoff_date)\
            .order("change_date", desc=True)\
            .limit(limit)\
            .execute()

        for e in (drug_events.data or []):
            event_type = "approval" if e.get("fda_approved_to") and not e.get("fda_approved_from") else "phase_change"
            events.append({
                "type": "drug",
                "event_type": event_type,
                "entity_id": e["drug_id"],
                "entity_name": e["drug_name"],
                "description": f"Entered Phase {e['phase_to']}" if event_type == "phase_change" else "FDA Approved",
                "date": str(e["change_date"]),
                "source": e.get("source"),
            })

        # Company events
        company_events = supabase.table("epi_company_entry_history")\
            .select("*")\
            .gte("event_date", cutoff_date)\
            .order("event_date", desc=True)\
            .limit(limit)\
            .execute()

        for e in (company_events.data or []):
            events.append({
                "type": "company",
                "event_type": e["event_type"],
                "entity_id": e["company_id"],
                "entity_name": e["company_name"],
                "description": e.get("event_description") or e["event_type"].replace("_", " ").title(),
                "date": str(e["event_date"]),
                "source": e.get("source"),
            })

        # Target events
        target_events = supabase.table("epi_target_activity_history")\
            .select("*")\
            .gte("event_date", cutoff_date)\
            .order("event_date", desc=True)\
            .limit(limit)\
            .execute()

        for e in (target_events.data or []):
            events.append({
                "type": "target",
                "event_type": e["event_type"],
                "entity_id": e["target_id"],
                "entity_name": e["target_symbol"],
                "description": f"{e.get('drug_name', 'Drug')} {e['event_type'].replace('_', ' ')}",
                "date": str(e["event_date"]),
                "source": e.get("source"),
            })

        # Sort all events by date
        events.sort(key=lambda x: x["date"], reverse=True)

        return {
            "events": events[:limit],
            "total_count": len(events),
            "cutoff_date": cutoff_date
        }

    except Exception as e:
        return {
            "events": [],
            "total_count": 0,
            "cutoff_date": cutoff_date,
            "error": str(e)
        }
