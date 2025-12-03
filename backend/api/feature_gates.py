"""
Feature Gates - Centralized feature access control
Defines what features are available at each subscription tier.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class SubscriptionTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class FeatureAccess(BaseModel):
    """Result of a feature access check."""
    allowed: bool
    reason: Optional[str] = None
    upgrade_tier: Optional[str] = None
    limit: Optional[int] = None
    used: Optional[int] = None


# ============================================
# Feature Definitions
# ============================================

# Features that are completely gated (boolean access)
GATED_FEATURES = {
    # Feature name: minimum tier required
    "full_scoring": SubscriptionTier.PRO,           # Bio/Chem/Tract scores
    "pipeline_phases": SubscriptionTier.PRO,        # Phase 1/2/3 data
    "exports_csv": SubscriptionTier.PRO,            # CSV exports
    "exports_excel": SubscriptionTier.PRO,          # Excel exports
    "exports_pptx": SubscriptionTier.PRO,           # PowerPoint exports
    "full_company_profiles": SubscriptionTier.PRO,  # Full company data
    "full_calendar": SubscriptionTier.PRO,          # Full calendar (not just 30 days)
    "full_news": SubscriptionTier.PRO,              # Full news (not just headlines)
    "alerts": SubscriptionTier.PRO,                 # Alert notifications
    "ai_chat": SubscriptionTier.PRO,                # AI chat feature
    "api_access": SubscriptionTier.ENTERPRISE,      # API programmatic access
    "sso_saml": SubscriptionTier.ENTERPRISE,        # SSO/SAML authentication
    "priority_support": SubscriptionTier.ENTERPRISE,# Priority support
    "custom_reports": SubscriptionTier.ENTERPRISE,  # Custom report requests
    "team_seats": SubscriptionTier.ENTERPRISE,      # Multiple team members
}

# Features with usage limits per tier
USAGE_LIMITS = {
    "watchlist_items": {
        SubscriptionTier.FREE: 5,
        SubscriptionTier.PRO: 50,
        SubscriptionTier.ENTERPRISE: -1,  # -1 = unlimited
    },
    "exports_per_month": {
        SubscriptionTier.FREE: 0,
        SubscriptionTier.PRO: 25,
        SubscriptionTier.ENTERPRISE: -1,
    },
    "pptx_exports_per_month": {
        SubscriptionTier.FREE: 0,
        SubscriptionTier.PRO: 5,
        SubscriptionTier.ENTERPRISE: -1,
    },
    "alerts_per_month": {
        SubscriptionTier.FREE: 0,
        SubscriptionTier.PRO: 10,
        SubscriptionTier.ENTERPRISE: -1,
    },
    "ai_questions_per_month": {
        SubscriptionTier.FREE: 0,
        SubscriptionTier.PRO: 50,
        SubscriptionTier.ENTERPRISE: -1,
    },
    "api_calls_per_month": {
        SubscriptionTier.FREE: 0,
        SubscriptionTier.PRO: 0,
        SubscriptionTier.ENTERPRISE: 10000,
    },
    "calendar_days_ahead": {
        SubscriptionTier.FREE: 30,
        SubscriptionTier.PRO: 365,
        SubscriptionTier.ENTERPRISE: 365,
    },
}

# Data visibility rules (what fields to hide/blur for free users)
DATA_VISIBILITY = {
    "drug_fields": {
        SubscriptionTier.FREE: ["id", "name", "chembl_id", "drug_type", "fda_approved"],
        SubscriptionTier.PRO: "*",  # All fields
        SubscriptionTier.ENTERPRISE: "*",
    },
    "target_fields": {
        SubscriptionTier.FREE: ["id", "symbol", "name", "family", "target_class"],
        SubscriptionTier.PRO: "*",
        SubscriptionTier.ENTERPRISE: "*",
    },
    "company_fields": {
        SubscriptionTier.FREE: ["id", "name", "ticker"],
        SubscriptionTier.PRO: "*",
        SubscriptionTier.ENTERPRISE: "*",
    },
    "news_fields": {
        SubscriptionTier.FREE: ["id", "title", "source", "pub_date"],  # Headlines only
        SubscriptionTier.PRO: "*",
        SubscriptionTier.ENTERPRISE: "*",
    },
}


# ============================================
# Feature Access Checker
# ============================================

class FeatureGateChecker:
    """Check if a user has access to features based on their subscription tier."""

    def __init__(self, user_tier: str, usage_stats: Optional[dict] = None):
        """
        Initialize the checker.

        Args:
            user_tier: The user's subscription tier (free, pro, enterprise)
            usage_stats: Dict of current usage counts (e.g., exports_this_month)
        """
        try:
            self.tier = SubscriptionTier(user_tier.lower())
        except ValueError:
            self.tier = SubscriptionTier.FREE

        self.usage_stats = usage_stats or {}

    def _get_tier_rank(self, tier: SubscriptionTier) -> int:
        """Get numeric rank for tier comparison."""
        ranks = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.PRO: 1,
            SubscriptionTier.ENTERPRISE: 2,
        }
        return ranks.get(tier, 0)

    def can_access(self, feature: str) -> FeatureAccess:
        """
        Check if user can access a gated feature.

        Args:
            feature: Feature name from GATED_FEATURES

        Returns:
            FeatureAccess with allowed status and upgrade info
        """
        if feature not in GATED_FEATURES:
            return FeatureAccess(allowed=True)

        required_tier = GATED_FEATURES[feature]
        user_rank = self._get_tier_rank(self.tier)
        required_rank = self._get_tier_rank(required_tier)

        if user_rank >= required_rank:
            return FeatureAccess(allowed=True)

        return FeatureAccess(
            allowed=False,
            reason=f"This feature requires {required_tier.value.title()} tier or higher",
            upgrade_tier=required_tier.value,
        )

    def get_limit(self, limit_name: str) -> int:
        """
        Get the usage limit for a feature.

        Args:
            limit_name: Limit name from USAGE_LIMITS

        Returns:
            The limit (-1 for unlimited)
        """
        if limit_name not in USAGE_LIMITS:
            return -1

        return USAGE_LIMITS[limit_name].get(self.tier, 0)

    def check_usage_limit(self, limit_name: str, current_usage: Optional[int] = None) -> FeatureAccess:
        """
        Check if user is within their usage limit.

        Args:
            limit_name: Limit name from USAGE_LIMITS
            current_usage: Current usage count (or from usage_stats if not provided)

        Returns:
            FeatureAccess with allowed status and usage info
        """
        limit = self.get_limit(limit_name)

        if current_usage is None:
            # Map limit names to usage stat keys
            stat_key_map = {
                "exports_per_month": "exports_this_month",
                "pptx_exports_per_month": "pptx_exports_this_month",
                "alerts_per_month": "alerts_this_month",
                "ai_questions_per_month": "ai_questions_this_month",
                "api_calls_per_month": "api_calls_this_month",
                "watchlist_items": "watchlist_count",
            }
            stat_key = stat_key_map.get(limit_name, limit_name)
            current_usage = self.usage_stats.get(stat_key, 0)

        # -1 means unlimited
        if limit == -1:
            return FeatureAccess(
                allowed=True,
                limit=-1,
                used=current_usage,
            )

        # 0 means not available at this tier
        if limit == 0:
            # Find the tier that has this feature
            upgrade_tier = None
            for tier in [SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE]:
                if USAGE_LIMITS[limit_name].get(tier, 0) > 0:
                    upgrade_tier = tier.value
                    break

            return FeatureAccess(
                allowed=False,
                reason=f"This feature is not available on the {self.tier.value.title()} tier",
                upgrade_tier=upgrade_tier,
                limit=0,
                used=current_usage,
            )

        # Check if within limit
        if current_usage < limit:
            return FeatureAccess(
                allowed=True,
                limit=limit,
                used=current_usage,
            )

        return FeatureAccess(
            allowed=False,
            reason=f"You've reached your monthly limit of {limit}",
            upgrade_tier="pro" if self.tier == SubscriptionTier.FREE else "enterprise",
            limit=limit,
            used=current_usage,
        )

    def get_visible_fields(self, entity_type: str) -> list[str]:
        """
        Get the list of visible fields for an entity type.

        Args:
            entity_type: One of drug_fields, target_fields, company_fields, news_fields

        Returns:
            List of field names or ["*"] for all fields
        """
        if entity_type not in DATA_VISIBILITY:
            return ["*"]

        return DATA_VISIBILITY[entity_type].get(self.tier, ["*"])

    def filter_entity(self, entity: dict, entity_type: str) -> dict:
        """
        Filter entity fields based on tier visibility.

        Args:
            entity: The entity dict to filter
            entity_type: One of drug_fields, target_fields, etc.

        Returns:
            Filtered entity dict
        """
        visible_fields = self.get_visible_fields(entity_type)

        if visible_fields == "*" or "*" in visible_fields:
            return entity

        # For fields that should be hidden, set to None or a placeholder
        filtered = {}
        for key, value in entity.items():
            if key in visible_fields:
                filtered[key] = value
            elif key in ["bio_score", "chem_score", "tractability_score", "total_score", "max_phase"]:
                # Scores and phase - indicate they're locked
                filtered[key] = None
                filtered[f"{key}_locked"] = True
            else:
                # Other fields - just exclude
                pass

        return filtered


# ============================================
# Pricing Tiers Definition
# ============================================

PRICING_TIERS = {
    "free": {
        "id": "free",
        "name": "Explorer",
        "description": "Basic access to browse epigenetic data",
        "price_monthly": 0,
        "price_yearly": 0,
        "features": [
            {"text": "Browse all 79 epigenetic targets", "included": True},
            {"text": "View approved drug profiles", "included": True},
            {"text": "Basic search functionality", "included": True},
            {"text": "5 watchlist items", "included": True},
            {"text": "Full drug scoring (Bio/Chem/Tract)", "included": False},
            {"text": "Pipeline phase data", "included": False},
            {"text": "Export data (CSV/Excel)", "included": False},
            {"text": "AI-powered insights", "included": False},
        ],
        "limits": {
            "watchlist": 5,
            "exports": 0,
            "ai_questions": 0,
            "calendar_days": 30,
        },
    },
    "pro": {
        "id": "pro",
        "name": "Analyst",
        "description": "Full intelligence for professionals",
        "price_monthly": 4900,  # $49.00
        "price_yearly": 39900,  # $399.00 (save $189)
        "features": [
            {"text": "Everything in Explorer", "included": True},
            {"text": "Full scoring (Bio/Chem/Tract)", "included": True},
            {"text": "Pipeline phase tracking", "included": True},
            {"text": "50 watchlist items", "included": True},
            {"text": "25 exports/month (CSV/Excel)", "included": True},
            {"text": "5 PowerPoint decks/month", "included": True},
            {"text": "50 AI questions/month", "included": True},
            {"text": "Full calendar & PDUFA dates", "included": True},
            {"text": "10 custom alerts/month", "included": True},
            {"text": "API access", "included": False},
        ],
        "limits": {
            "watchlist": 50,
            "exports": 25,
            "pptx_exports": 5,
            "ai_questions": 50,
            "alerts": 10,
            "calendar_days": 365,
        },
    },
    "enterprise": {
        "id": "enterprise",
        "name": "Enterprise",
        "description": "Unlimited access for teams",
        "price_monthly": 49900,  # $499.00
        "price_yearly": 399900,  # $3,999.00 (save $1,989)
        "features": [
            {"text": "Everything in Analyst", "included": True},
            {"text": "Unlimited watchlist & exports", "included": True},
            {"text": "Unlimited AI questions", "included": True},
            {"text": "Unlimited custom alerts", "included": True},
            {"text": "API access (10,000 calls/mo)", "included": True},
            {"text": "SSO/SAML integration", "included": True},
            {"text": "Priority support", "included": True},
            {"text": "Custom report requests", "included": True},
            {"text": "Up to 10 team seats", "included": True},
        ],
        "limits": {
            "watchlist": -1,
            "exports": -1,
            "pptx_exports": -1,
            "ai_questions": -1,
            "alerts": -1,
            "api_calls": 10000,
            "team_seats": 10,
        },
    },
}


def get_pricing_tiers() -> list[dict]:
    """Get all pricing tiers for display."""
    return list(PRICING_TIERS.values())


def get_tier_info(tier_id: str) -> Optional[dict]:
    """Get info for a specific tier."""
    return PRICING_TIERS.get(tier_id)
