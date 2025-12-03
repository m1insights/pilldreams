"""
Watchlist API Endpoints
Week 4: User watchlist management and alerts
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/watchlist", tags=["watchlist"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ============================================
# Pydantic Models
# ============================================

class WatchlistItemCreate(BaseModel):
    entity_type: str  # 'drug', 'target', 'company', 'trial', 'indication'
    entity_id: str
    entity_name: str
    alert_on_phase_change: bool = True
    alert_on_status_change: bool = True
    alert_on_score_change: bool = True
    alert_on_news: bool = True
    alert_on_patent: bool = False
    alert_on_pdufa: bool = True
    notes: Optional[str] = None


class WatchlistItemUpdate(BaseModel):
    alert_on_phase_change: Optional[bool] = None
    alert_on_status_change: Optional[bool] = None
    alert_on_score_change: Optional[bool] = None
    alert_on_news: Optional[bool] = None
    alert_on_patent: Optional[bool] = None
    alert_on_pdufa: Optional[bool] = None
    alert_email: Optional[bool] = None
    alert_slack: Optional[bool] = None
    alert_in_app: Optional[bool] = None
    notes: Optional[str] = None


class WatchlistItem(BaseModel):
    id: str
    user_id: str
    entity_type: str
    entity_id: str
    entity_name: str
    alert_on_phase_change: bool
    alert_on_status_change: bool
    alert_on_score_change: bool
    alert_on_news: bool
    alert_on_patent: bool
    alert_on_pdufa: bool
    alert_email: bool
    alert_slack: bool
    alert_in_app: bool
    notes: Optional[str]
    created_at: datetime


class Alert(BaseModel):
    id: str
    alert_type: str
    alert_title: str
    alert_body: Optional[str]
    alert_url: Optional[str]
    significance: str
    status: str
    created_at: datetime


class NotificationPrefs(BaseModel):
    email_enabled: bool = True
    email_frequency: str = "realtime"
    email_min_significance: str = "high"
    slack_enabled: bool = False
    slack_webhook_url: Optional[str] = None
    slack_min_significance: str = "critical"
    in_app_enabled: bool = True
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    timezone: str = "America/New_York"


# ============================================
# Helper: Get current user (mock for now)
# ============================================

async def get_current_user_id() -> str:
    """
    Get the current user ID from the request.
    In production, this would validate the JWT token.
    For now, return a mock user ID.
    """
    # TODO: Implement proper JWT validation with Supabase Auth
    return "00000000-0000-0000-0000-000000000001"


# ============================================
# Watchlist Endpoints
# ============================================

@router.get("/", response_model=List[WatchlistItem])
async def get_watchlist(
    entity_type: Optional[str] = None,
    user_id: str = Depends(get_current_user_id)
):
    """Get all items in user's watchlist."""
    try:
        query = supabase.table("ci_watchlist").select("*").eq("user_id", user_id)

        if entity_type:
            query = query.eq("entity_type", entity_type)

        result = query.order("created_at", desc=True).execute()
        return result.data or []
    except Exception as e:
        if "PGRST205" in str(e):
            return []  # Table doesn't exist yet
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=WatchlistItem)
async def add_to_watchlist(
    item: WatchlistItemCreate,
    user_id: str = Depends(get_current_user_id)
):
    """Add an entity to the watchlist."""
    try:
        # Check if already watching
        existing = supabase.table("ci_watchlist").select("id").eq(
            "user_id", user_id
        ).eq(
            "entity_type", item.entity_type
        ).eq(
            "entity_id", item.entity_id
        ).execute()

        if existing.data:
            raise HTTPException(status_code=400, detail="Entity already in watchlist")

        # Insert new item
        result = supabase.table("ci_watchlist").insert({
            "user_id": user_id,
            "entity_type": item.entity_type,
            "entity_id": item.entity_id,
            "entity_name": item.entity_name,
            "alert_on_phase_change": item.alert_on_phase_change,
            "alert_on_status_change": item.alert_on_status_change,
            "alert_on_score_change": item.alert_on_score_change,
            "alert_on_news": item.alert_on_news,
            "alert_on_patent": item.alert_on_patent,
            "alert_on_pdufa": item.alert_on_pdufa,
            "notes": item.notes
        }).execute()

        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{watchlist_id}", response_model=WatchlistItem)
async def update_watchlist_item(
    watchlist_id: str,
    updates: WatchlistItemUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """Update watchlist item preferences."""
    try:
        # Build update dict with only non-None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        update_data["updated_at"] = datetime.now().isoformat()

        result = supabase.table("ci_watchlist").update(update_data).eq(
            "id", watchlist_id
        ).eq(
            "user_id", user_id
        ).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Watchlist item not found")

        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{watchlist_id}")
async def remove_from_watchlist(
    watchlist_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Remove an entity from the watchlist."""
    try:
        result = supabase.table("ci_watchlist").delete().eq(
            "id", watchlist_id
        ).eq(
            "user_id", user_id
        ).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Watchlist item not found")

        return {"status": "removed", "id": watchlist_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Alert Endpoints
# ============================================

@router.get("/alerts", response_model=List[Alert])
async def get_alerts(
    status: Optional[str] = None,
    limit: int = 50,
    user_id: str = Depends(get_current_user_id)
):
    """Get user's alerts."""
    try:
        query = supabase.table("ci_alert_queue").select("*").eq("user_id", user_id)

        if status:
            query = query.eq("status", status)

        result = query.order("created_at", desc=True).limit(limit).execute()
        return result.data or []
    except Exception as e:
        if "PGRST205" in str(e):
            return []
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/unread/count")
async def get_unread_alert_count(
    user_id: str = Depends(get_current_user_id)
):
    """Get count of unread alerts."""
    try:
        result = supabase.table("ci_alert_queue").select(
            "id", count="exact"
        ).eq(
            "user_id", user_id
        ).eq(
            "status", "sent"
        ).execute()

        return {"unread_count": result.count or 0}
    except Exception as e:
        if "PGRST205" in str(e):
            return {"unread_count": 0}
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Mark an alert as read."""
    try:
        result = supabase.table("ci_alert_queue").update({
            "status": "read",
            "read_at": datetime.now().isoformat()
        }).eq(
            "id", alert_id
        ).eq(
            "user_id", user_id
        ).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Alert not found")

        return {"status": "read", "id": alert_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/alerts/{alert_id}/dismiss")
async def dismiss_alert(
    alert_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Dismiss an alert."""
    try:
        result = supabase.table("ci_alert_queue").update({
            "status": "dismissed"
        }).eq(
            "id", alert_id
        ).eq(
            "user_id", user_id
        ).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Alert not found")

        return {"status": "dismissed", "id": alert_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Notification Preferences
# ============================================

@router.get("/notifications/preferences", response_model=NotificationPrefs)
async def get_notification_preferences(
    user_id: str = Depends(get_current_user_id)
):
    """Get user's notification preferences."""
    try:
        result = supabase.table("ci_notification_prefs").select("*").eq(
            "user_id", user_id
        ).execute()

        if result.data:
            return result.data[0]

        # Return defaults if no prefs exist
        return NotificationPrefs()
    except Exception as e:
        if "PGRST205" in str(e):
            return NotificationPrefs()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/preferences", response_model=NotificationPrefs)
async def update_notification_preferences(
    prefs: NotificationPrefs,
    user_id: str = Depends(get_current_user_id)
):
    """Update user's notification preferences."""
    try:
        data = prefs.dict()
        data["user_id"] = user_id
        data["updated_at"] = datetime.now().isoformat()

        result = supabase.table("ci_notification_prefs").upsert(
            data, on_conflict="user_id"
        ).execute()

        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
