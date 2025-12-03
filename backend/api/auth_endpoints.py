"""
Auth API Endpoints
Week 6: Supabase Auth integration with user profiles
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
from supabase import create_client, Client
from dotenv import load_dotenv

from .feature_gates import (
    FeatureGateChecker,
    FeatureAccess,
    GATED_FEATURES,
    USAGE_LIMITS,
    get_pricing_tiers,
    get_tier_info,
)

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Auth"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ============================================
# Pydantic Models
# ============================================

class UserProfile(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    subscription_tier: str = "free"
    subscription_status: str = "active"
    trial_ends_at: Optional[datetime] = None
    api_calls_this_month: int = 0
    api_calls_limit: int = 100
    exports_this_month: int = 0
    exports_limit: int = 5


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None


class SubscriptionTier(BaseModel):
    id: str
    name: str
    description: Optional[str]
    price_monthly: Optional[int]
    price_yearly: Optional[int]
    api_calls_limit: Optional[int]
    exports_limit: Optional[int]
    watchlist_limit: Optional[int]
    alerts_limit: Optional[int]
    feature_exports: bool
    feature_api_access: bool
    feature_slack_alerts: bool
    is_popular: bool


class UsageStats(BaseModel):
    api_calls_used: int
    api_calls_limit: int
    api_calls_percent: float
    exports_used: int
    exports_limit: int
    exports_percent: float
    can_export: bool
    can_api: bool


# ============================================
# Helper: Get current user from JWT
# ============================================

async def get_current_user(request: Request) -> Optional[str]:
    """
    Extract and validate user from Authorization header.
    Returns user_id if valid, None otherwise.
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.replace("Bearer ", "")

    try:
        # Verify JWT with Supabase
        user = supabase.auth.get_user(token)
        if user and user.user:
            return user.user.id
    except Exception:
        pass

    return None


async def require_auth(request: Request) -> str:
    """Require authentication - raises 401 if not authenticated."""
    user_id = await get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


# ============================================
# Auth Endpoints
# ============================================

@router.get("/me", response_model=UserProfile)
async def get_current_profile(user_id: str = Depends(require_auth)):
    """Get the current user's profile."""
    try:
        result = supabase.table("ci_user_profiles").select("*").eq(
            "id", user_id
        ).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Profile not found")

        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/me", response_model=UserProfile)
async def update_profile(
    updates: UserProfileUpdate,
    user_id: str = Depends(require_auth)
):
    """Update the current user's profile."""
    try:
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        update_data["updated_at"] = datetime.now().isoformat()

        result = supabase.table("ci_user_profiles").update(update_data).eq(
            "id", user_id
        ).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Profile not found")

        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me/usage", response_model=UsageStats)
async def get_usage_stats(user_id: str = Depends(require_auth)):
    """Get the current user's usage statistics."""
    try:
        result = supabase.table("ci_user_profiles").select(
            "api_calls_this_month, api_calls_limit, exports_this_month, exports_limit, subscription_tier"
        ).eq("id", user_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Profile not found")

        profile = result.data[0]

        # Calculate percentages (-1 limit means unlimited)
        api_limit = profile["api_calls_limit"]
        exports_limit = profile["exports_limit"]

        api_percent = 0 if api_limit == -1 else (profile["api_calls_this_month"] / api_limit * 100 if api_limit > 0 else 100)
        exports_percent = 0 if exports_limit == -1 else (profile["exports_this_month"] / exports_limit * 100 if exports_limit > 0 else 100)

        # Check if can perform actions
        can_export = exports_limit == -1 or profile["exports_this_month"] < exports_limit
        can_api = api_limit == -1 or profile["api_calls_this_month"] < api_limit

        return UsageStats(
            api_calls_used=profile["api_calls_this_month"],
            api_calls_limit=api_limit,
            api_calls_percent=min(api_percent, 100),
            exports_used=profile["exports_this_month"],
            exports_limit=exports_limit,
            exports_percent=min(exports_percent, 100),
            can_export=can_export,
            can_api=can_api
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/me/track-login")
async def track_login(user_id: str = Depends(require_auth)):
    """Track user login timestamp."""
    try:
        supabase.table("ci_user_profiles").update({
            "last_login_at": datetime.now().isoformat()
        }).eq("id", user_id).execute()

        return {"status": "tracked"}
    except Exception as e:
        # Don't fail login tracking
        return {"status": "error", "message": str(e)}


# ============================================
# Subscription Tiers (Public)
# ============================================

@router.get("/tiers", response_model=list[SubscriptionTier])
async def get_subscription_tiers():
    """Get all subscription tiers (public endpoint)."""
    try:
        result = supabase.table("ci_subscription_tiers").select("*").order(
            "display_order"
        ).execute()

        return result.data or []
    except Exception as e:
        if "PGRST205" in str(e):
            # Return default tiers if table doesn't exist
            return [
                {
                    "id": "free",
                    "name": "Free",
                    "description": "Basic access",
                    "price_monthly": 0,
                    "price_yearly": 0,
                    "api_calls_limit": 100,
                    "exports_limit": 5,
                    "watchlist_limit": 10,
                    "alerts_limit": 50,
                    "feature_exports": False,
                    "feature_api_access": False,
                    "feature_slack_alerts": False,
                    "is_popular": False
                },
                {
                    "id": "pro",
                    "name": "Pro",
                    "description": "Full access for professionals",
                    "price_monthly": 4900,
                    "price_yearly": 39900,
                    "api_calls_limit": 1000,
                    "exports_limit": 50,
                    "watchlist_limit": 100,
                    "alerts_limit": 500,
                    "feature_exports": True,
                    "feature_api_access": True,
                    "feature_slack_alerts": True,
                    "is_popular": True
                },
                {
                    "id": "enterprise",
                    "name": "Enterprise",
                    "description": "Unlimited for teams",
                    "price_monthly": 19900,
                    "price_yearly": 159900,
                    "api_calls_limit": -1,
                    "exports_limit": -1,
                    "watchlist_limit": -1,
                    "alerts_limit": -1,
                    "feature_exports": True,
                    "feature_api_access": True,
                    "feature_slack_alerts": True,
                    "is_popular": False
                }
            ]
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Feature Access Check
# ============================================

@router.get("/me/can-access/{feature}")
async def check_feature_access(
    feature: str,
    user_id: str = Depends(require_auth)
):
    """
    Check if user can access a specific feature.

    Features include:
    - full_scoring: Bio/Chem/Tract scores
    - pipeline_phases: Phase 1/2/3 data
    - exports_csv, exports_excel, exports_pptx: Export functionality
    - full_company_profiles: Complete company data
    - full_calendar: Full calendar (not just 30 days)
    - full_news: Full news content (not just headlines)
    - alerts: Alert notifications
    - ai_chat: AI chat feature
    - api_access: API programmatic access
    - sso_saml: SSO/SAML authentication
    - priority_support: Priority support
    """
    try:
        # Get user's tier and usage stats
        profile = supabase.table("ci_user_profiles").select(
            "subscription_tier, exports_this_month, api_calls_this_month"
        ).eq("id", user_id).execute()

        if not profile.data:
            return {
                "allowed": False,
                "reason": "Profile not found",
                "upgrade_tier": "free"
            }

        profile_data = profile.data[0]
        tier = profile_data.get("subscription_tier", "free")

        # Build usage stats
        usage_stats = {
            "exports_this_month": profile_data.get("exports_this_month", 0),
            "api_calls_this_month": profile_data.get("api_calls_this_month", 0),
        }

        # Use the feature gate checker
        checker = FeatureGateChecker(tier, usage_stats)
        result = checker.can_access(feature)

        return {
            "allowed": result.allowed,
            "reason": result.reason,
            "upgrade_tier": result.upgrade_tier,
            "current_tier": tier,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me/check-limit/{limit_name}")
async def check_usage_limit(
    limit_name: str,
    user_id: str = Depends(require_auth)
):
    """
    Check if user is within their usage limit for a feature.

    Limits include:
    - watchlist_items
    - exports_per_month
    - pptx_exports_per_month
    - alerts_per_month
    - ai_questions_per_month
    - api_calls_per_month
    """
    try:
        # Get user's tier and relevant usage stats
        profile = supabase.table("ci_user_profiles").select(
            "subscription_tier, exports_this_month, api_calls_this_month"
        ).eq("id", user_id).execute()

        if not profile.data:
            return {
                "allowed": False,
                "reason": "Profile not found",
            }

        profile_data = profile.data[0]
        tier = profile_data.get("subscription_tier", "free")

        # Get watchlist count if checking watchlist limit
        usage_stats = {
            "exports_this_month": profile_data.get("exports_this_month", 0),
            "api_calls_this_month": profile_data.get("api_calls_this_month", 0),
        }

        if limit_name == "watchlist_items":
            # Count watchlist items
            watchlist = supabase.table("ci_watchlist").select(
                "id", count="exact"
            ).eq("user_id", user_id).execute()
            usage_stats["watchlist_count"] = watchlist.count or 0

        # Use the feature gate checker
        checker = FeatureGateChecker(tier, usage_stats)
        result = checker.check_usage_limit(limit_name)

        return {
            "allowed": result.allowed,
            "reason": result.reason,
            "upgrade_tier": result.upgrade_tier,
            "limit": result.limit,
            "used": result.used,
            "current_tier": tier,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me/all-limits")
async def get_all_limits(user_id: str = Depends(require_auth)):
    """Get all usage limits and current usage for the user."""
    try:
        # Get user's tier and usage stats
        profile = supabase.table("ci_user_profiles").select("*").eq(
            "id", user_id
        ).execute()

        if not profile.data:
            raise HTTPException(status_code=404, detail="Profile not found")

        profile_data = profile.data[0]
        tier = profile_data.get("subscription_tier", "free")

        # Get watchlist count
        watchlist = supabase.table("ci_watchlist").select(
            "id", count="exact"
        ).eq("user_id", user_id).execute()
        watchlist_count = watchlist.count or 0

        usage_stats = {
            "exports_this_month": profile_data.get("exports_this_month", 0),
            "pptx_exports_this_month": profile_data.get("pptx_exports_this_month", 0),
            "ai_questions_this_month": profile_data.get("ai_questions_this_month", 0),
            "alerts_this_month": profile_data.get("alerts_this_month", 0),
            "api_calls_this_month": profile_data.get("api_calls_this_month", 0),
            "watchlist_count": watchlist_count,
        }

        checker = FeatureGateChecker(tier, usage_stats)

        # Check all limits
        limits = {}
        for limit_name in USAGE_LIMITS.keys():
            result = checker.check_usage_limit(limit_name)
            limits[limit_name] = {
                "allowed": result.allowed,
                "limit": result.limit,
                "used": result.used,
            }

        return {
            "tier": tier,
            "limits": limits,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features")
async def get_all_features():
    """Get list of all gated features and what tier they require."""
    return {
        "gated_features": {
            feature: tier.value for feature, tier in GATED_FEATURES.items()
        },
        "usage_limits": {
            name: {tier.value: limit for tier, limit in tiers.items()}
            for name, tiers in USAGE_LIMITS.items()
        },
    }


@router.post("/me/increment-usage/{usage_type}")
async def increment_usage(
    usage_type: str,
    user_id: str = Depends(require_auth)
):
    """
    Increment usage counter for a feature.
    Used internally by other endpoints when features are used.

    Usage types: exports, pptx_exports, ai_questions, alerts, api_calls
    """
    valid_types = ["exports", "pptx_exports", "ai_questions", "alerts", "api_calls"]

    if usage_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid usage type. Valid: {valid_types}"
        )

    try:
        column_name = f"{usage_type}_this_month"

        # Get current value
        profile = supabase.table("ci_user_profiles").select(
            column_name
        ).eq("id", user_id).execute()

        if not profile.data:
            raise HTTPException(status_code=404, detail="Profile not found")

        current = profile.data[0].get(column_name, 0)

        # Increment
        supabase.table("ci_user_profiles").update({
            column_name: current + 1,
            "updated_at": datetime.now().isoformat(),
        }).eq("id", user_id).execute()

        return {"status": "incremented", "new_value": current + 1}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
