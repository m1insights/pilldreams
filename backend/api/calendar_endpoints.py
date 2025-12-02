"""
Clinical Trial Calendar API Endpoints

Provides access to trial readout dates, phases, and status from ClinicalTrials.gov.
Includes date confidence computation for UI indicators.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Literal
from pydantic import BaseModel
from datetime import datetime, timedelta
from backend.etl.supabase_client import supabase

router = APIRouter(prefix="/calendar", tags=["Trial Calendar"])


# ============ Date Confidence Logic ============

def compute_date_confidence(
    primary_completion_date: Optional[str],
    primary_completion_type: Optional[str]
) -> str:
    """
    Compute confidence level for a trial's primary completion date.

    Returns:
        - "confirmed": Actual completion date (trial completed)
        - "estimated": Anticipated date (reasonable confidence)
        - "placeholder": Year-end/start dates (low confidence)
        - "unknown": No date available
    """
    if not primary_completion_date:
        return "unknown"

    if primary_completion_type == "ACTUAL":
        return "confirmed"

    # Check for year-end/start placeholders
    date_str = str(primary_completion_date)
    if date_str.endswith("-12-31") or date_str.endswith("-01-01"):
        return "placeholder"

    # Check for quarter-end dates (also common placeholders)
    if date_str.endswith("-03-31") or date_str.endswith("-06-30") or date_str.endswith("-09-30"):
        return "estimated"  # Could be real quarter-end, but less suspicious

    return "estimated"


def get_confidence_tooltip(confidence: str) -> str:
    """Get human-readable tooltip for confidence level."""
    tooltips = {
        "confirmed": "Trial completed - date confirmed",
        "estimated": "Anticipated date - may shift ±1-3 months",
        "placeholder": "Year-end placeholder - low confidence, actual date likely differs",
        "unknown": "No completion date provided"
    }
    return tooltips.get(confidence, "Unknown")


# ============ Pydantic Models ============

class TrialSummary(BaseModel):
    id: str
    nct_id: str
    trial_title: Optional[str] = None
    drug_id: Optional[str] = None
    drug_name: Optional[str] = None
    phase: Optional[str] = None
    status: Optional[str] = None
    primary_completion_date: Optional[str] = None
    primary_completion_type: Optional[str] = None
    date_confidence: str  # "confirmed", "estimated", "placeholder", "unknown"
    date_confidence_tooltip: str
    lead_sponsor: Optional[str] = None
    lead_sponsor_type: Optional[str] = None
    enrollment: Optional[int] = None


class TrialDetail(BaseModel):
    id: str
    nct_id: str
    trial_title: Optional[str] = None
    drug_id: Optional[str] = None
    drug_name: Optional[str] = None
    phase: Optional[str] = None
    status: Optional[str] = None
    primary_completion_date: Optional[str] = None
    primary_completion_type: Optional[str] = None
    study_completion_date: Optional[str] = None
    study_completion_type: Optional[str] = None
    start_date: Optional[str] = None
    date_confidence: str
    date_confidence_tooltip: str
    lead_sponsor: Optional[str] = None
    lead_sponsor_type: Optional[str] = None
    collaborators: Optional[List[str]] = None
    enrollment: Optional[int] = None
    enrollment_type: Optional[str] = None
    study_type: Optional[str] = None
    indication_id: Optional[str] = None
    indication_name: Optional[str] = None
    source_url: Optional[str] = None
    query_tier: Optional[str] = None
    last_api_update: Optional[str] = None


class CalendarStats(BaseModel):
    total_trials: int
    by_phase: dict
    by_status: dict
    by_date_confidence: dict
    upcoming_30_days: int
    upcoming_90_days: int


class ConferenceSummary(BaseModel):
    id: str
    name: str
    short_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    abstract_deadline: Optional[str] = None
    year: int
    location: Optional[str] = None
    oncology_focus: bool = True
    epigenetics_track: bool = False


# ============ Trials Endpoints ============

@router.get("/trials", response_model=List[TrialSummary])
async def list_trials(
    phase: Optional[str] = Query(None, description="Filter by phase (PHASE1, PHASE2, PHASE3, PHASE4)"),
    status: Optional[str] = Query(None, description="Filter by status (RECRUITING, COMPLETED, etc.)"),
    drug_id: Optional[str] = Query(None, description="Filter by drug UUID"),
    drug_name: Optional[str] = Query(None, description="Filter by drug name (partial match)"),
    date_from: Optional[str] = Query(None, description="Primary completion date from (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Primary completion date to (YYYY-MM-DD)"),
    date_confidence: Optional[str] = Query(None, description="Filter by date confidence (confirmed, estimated, placeholder)"),
    exclude_placeholders: bool = Query(False, description="Exclude year-end placeholder dates"),
    limit: int = Query(100, le=500, description="Maximum results"),
    offset: int = Query(0, description="Offset for pagination")
):
    """
    List clinical trials with filtering and date confidence indicators.

    Date confidence levels:
    - confirmed (🟢): Trial completed, date is actual
    - estimated (🟡): Anticipated date, reasonable confidence
    - placeholder (🔴): Year-end/start date, low confidence
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        query = supabase.table("ci_trial_calendar").select("*")

        if phase:
            query = query.eq("phase", phase)
        if status:
            query = query.eq("status", status)
        if drug_id:
            query = query.eq("drug_id", drug_id)
        if drug_name:
            query = query.ilike("drug_name", f"%{drug_name}%")
        if date_from:
            query = query.gte("primary_completion_date", date_from)
        if date_to:
            query = query.lte("primary_completion_date", date_to)

        trials = query.order("primary_completion_date").range(offset, offset + limit - 1).execute().data

        result = []
        for t in trials:
            confidence = compute_date_confidence(
                t.get("primary_completion_date"),
                t.get("primary_completion_type")
            )

            # Skip placeholders if requested
            if exclude_placeholders and confidence == "placeholder":
                continue

            # Filter by confidence if specified
            if date_confidence and confidence != date_confidence:
                continue

            result.append(TrialSummary(
                id=t["id"],
                nct_id=t["nct_id"],
                trial_title=t.get("trial_title"),
                drug_id=t.get("drug_id"),
                drug_name=t.get("drug_name"),
                phase=t.get("phase"),
                status=t.get("status"),
                primary_completion_date=str(t["primary_completion_date"]) if t.get("primary_completion_date") else None,
                primary_completion_type=t.get("primary_completion_type"),
                date_confidence=confidence,
                date_confidence_tooltip=get_confidence_tooltip(confidence),
                lead_sponsor=t.get("lead_sponsor"),
                lead_sponsor_type=t.get("lead_sponsor_type"),
                enrollment=t.get("enrollment")
            ))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trials: {str(e)}")


@router.get("/trials/upcoming", response_model=List[TrialSummary])
async def get_upcoming_trials(
    days: int = Query(90, le=365, description="Look ahead days"),
    phase_min: int = Query(1, ge=0, le=4, description="Minimum phase (1=Phase 1, 2=Phase 2, etc.)"),
    exclude_placeholders: bool = Query(True, description="Exclude year-end placeholder dates"),
    limit: int = Query(50, le=200)
):
    """
    Get upcoming trial readouts within the specified time window.

    By default excludes year-end placeholder dates for cleaner results.
    High-value readouts (Phase 2/3) can be prioritized with phase_min=2.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        today = datetime.now().strftime("%Y-%m-%d")
        future = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

        # Map phase_min to phase filter
        phases = []
        if phase_min <= 1:
            phases = ["EARLY_PHASE1", "PHASE1", "PHASE2", "PHASE3", "PHASE4"]
        elif phase_min == 2:
            phases = ["PHASE2", "PHASE3", "PHASE4"]
        elif phase_min == 3:
            phases = ["PHASE3", "PHASE4"]
        elif phase_min == 4:
            phases = ["PHASE4"]

        query = supabase.table("ci_trial_calendar")\
            .select("*")\
            .gte("primary_completion_date", today)\
            .lte("primary_completion_date", future)\
            .in_("phase", phases)\
            .order("primary_completion_date")

        trials = query.limit(limit * 2).execute().data  # Fetch extra in case of filtering

        result = []
        for t in trials:
            if len(result) >= limit:
                break

            confidence = compute_date_confidence(
                t.get("primary_completion_date"),
                t.get("primary_completion_type")
            )

            # Skip placeholders if requested
            if exclude_placeholders and confidence == "placeholder":
                continue

            result.append(TrialSummary(
                id=t["id"],
                nct_id=t["nct_id"],
                trial_title=t.get("trial_title"),
                drug_id=t.get("drug_id"),
                drug_name=t.get("drug_name"),
                phase=t.get("phase"),
                status=t.get("status"),
                primary_completion_date=str(t["primary_completion_date"]) if t.get("primary_completion_date") else None,
                primary_completion_type=t.get("primary_completion_type"),
                date_confidence=confidence,
                date_confidence_tooltip=get_confidence_tooltip(confidence),
                lead_sponsor=t.get("lead_sponsor"),
                lead_sponsor_type=t.get("lead_sponsor_type"),
                enrollment=t.get("enrollment")
            ))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching upcoming trials: {str(e)}")


@router.get("/trials/{nct_id}", response_model=TrialDetail)
async def get_trial(nct_id: str):
    """Get detailed trial information by NCT ID."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        result = supabase.table("ci_trial_calendar")\
            .select("*")\
            .eq("nct_id", nct_id)\
            .single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail=f"Trial {nct_id} not found")

        t = result.data
        confidence = compute_date_confidence(
            t.get("primary_completion_date"),
            t.get("primary_completion_type")
        )

        return TrialDetail(
            id=t["id"],
            nct_id=t["nct_id"],
            trial_title=t.get("trial_title"),
            drug_id=t.get("drug_id"),
            drug_name=t.get("drug_name"),
            phase=t.get("phase"),
            status=t.get("status"),
            primary_completion_date=str(t["primary_completion_date"]) if t.get("primary_completion_date") else None,
            primary_completion_type=t.get("primary_completion_type"),
            study_completion_date=str(t["study_completion_date"]) if t.get("study_completion_date") else None,
            study_completion_type=t.get("study_completion_type"),
            start_date=str(t["start_date"]) if t.get("start_date") else None,
            date_confidence=confidence,
            date_confidence_tooltip=get_confidence_tooltip(confidence),
            lead_sponsor=t.get("lead_sponsor"),
            lead_sponsor_type=t.get("lead_sponsor_type"),
            collaborators=t.get("collaborators"),
            enrollment=t.get("enrollment"),
            enrollment_type=t.get("enrollment_type"),
            study_type=t.get("study_type"),
            indication_id=t.get("indication_id"),
            indication_name=t.get("indication_name"),
            source_url=t.get("source_url") or f"https://clinicaltrials.gov/study/{nct_id}",
            query_tier=t.get("query_tier"),
            last_api_update=str(t["last_api_update"]) if t.get("last_api_update") else None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trial: {str(e)}")


@router.get("/stats", response_model=CalendarStats)
async def get_calendar_stats():
    """Get summary statistics for the trial calendar."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        # Get all trials
        trials = supabase.table("ci_trial_calendar").select(
            "phase, status, primary_completion_date, primary_completion_type"
        ).execute().data

        total = len(trials)

        # Count by phase
        phases = {}
        for t in trials:
            p = t.get("phase") or "Unknown"
            phases[p] = phases.get(p, 0) + 1

        # Count by status
        statuses = {}
        for t in trials:
            s = t.get("status") or "Unknown"
            statuses[s] = statuses.get(s, 0) + 1

        # Count by date confidence
        confidences = {"confirmed": 0, "estimated": 0, "placeholder": 0, "unknown": 0}
        for t in trials:
            conf = compute_date_confidence(
                t.get("primary_completion_date"),
                t.get("primary_completion_type")
            )
            confidences[conf] = confidences.get(conf, 0) + 1

        # Count upcoming
        today = datetime.now().strftime("%Y-%m-%d")
        day30 = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        day90 = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")

        upcoming_30 = sum(
            1 for t in trials
            if t.get("primary_completion_date") and today <= str(t["primary_completion_date"]) <= day30
        )
        upcoming_90 = sum(
            1 for t in trials
            if t.get("primary_completion_date") and today <= str(t["primary_completion_date"]) <= day90
        )

        return CalendarStats(
            total_trials=total,
            by_phase=phases,
            by_status=statuses,
            by_date_confidence=confidences,
            upcoming_30_days=upcoming_30,
            upcoming_90_days=upcoming_90
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


# ============ Drug Trials Endpoint ============

@router.get("/drugs/{drug_id}/trials", response_model=List[TrialSummary])
async def get_drug_trials(
    drug_id: str,
    status: Optional[str] = None,
    exclude_placeholders: bool = Query(False)
):
    """Get all trials for a specific drug."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        query = supabase.table("ci_trial_calendar")\
            .select("*")\
            .eq("drug_id", drug_id)\
            .order("primary_completion_date")

        if status:
            query = query.eq("status", status)

        trials = query.execute().data

        result = []
        for t in trials:
            confidence = compute_date_confidence(
                t.get("primary_completion_date"),
                t.get("primary_completion_type")
            )

            if exclude_placeholders and confidence == "placeholder":
                continue

            result.append(TrialSummary(
                id=t["id"],
                nct_id=t["nct_id"],
                trial_title=t.get("trial_title"),
                drug_id=t.get("drug_id"),
                drug_name=t.get("drug_name"),
                phase=t.get("phase"),
                status=t.get("status"),
                primary_completion_date=str(t["primary_completion_date"]) if t.get("primary_completion_date") else None,
                primary_completion_type=t.get("primary_completion_type"),
                date_confidence=confidence,
                date_confidence_tooltip=get_confidence_tooltip(confidence),
                lead_sponsor=t.get("lead_sponsor"),
                lead_sponsor_type=t.get("lead_sponsor_type"),
                enrollment=t.get("enrollment")
            ))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching drug trials: {str(e)}")


# ============ Conferences Endpoints ============

@router.get("/conferences", response_model=List[ConferenceSummary])
async def list_conferences(
    year: Optional[int] = None,
    upcoming_only: bool = Query(True, description="Only show future conferences")
):
    """List oncology conferences."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        query = supabase.table("ci_conferences").select("*")

        if year:
            query = query.eq("year", year)

        if upcoming_only:
            today = datetime.now().strftime("%Y-%m-%d")
            query = query.gte("start_date", today)

        conferences = query.order("start_date").execute().data

        return [
            ConferenceSummary(
                id=c["id"],
                name=c["name"],
                short_name=c.get("short_name"),
                start_date=str(c["start_date"]) if c.get("start_date") else None,
                end_date=str(c["end_date"]) if c.get("end_date") else None,
                abstract_deadline=str(c["abstract_deadline"]) if c.get("abstract_deadline") else None,
                year=c["year"],
                location=c.get("location"),
                oncology_focus=c.get("oncology_focus", True),
                epigenetics_track=c.get("epigenetics_track", False)
            )
            for c in conferences
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching conferences: {str(e)}")
