"""
Payments API Endpoints
Week 6: Stripe integration for subscriptions
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Header
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os
import stripe
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/payments", tags=["payments"])

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Stripe setup
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


# ============================================
# Pydantic Models
# ============================================

class CreateCheckoutSession(BaseModel):
    tier_id: str  # 'pro' or 'enterprise'
    billing_period: str = "monthly"  # 'monthly' or 'yearly'
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CreatePortalSession(BaseModel):
    return_url: Optional[str] = None


class SubscriptionStatus(BaseModel):
    tier: str
    status: str
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    stripe_subscription_id: Optional[str] = None


class PaymentHistoryItem(BaseModel):
    id: str
    amount: int
    currency: str
    status: str
    description: Optional[str]
    created_at: datetime
    receipt_url: Optional[str]


# ============================================
# Helper: Get current user
# ============================================

async def get_current_user(request: Request) -> Optional[str]:
    """Extract user from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.replace("Bearer ", "")
    try:
        user = supabase.auth.get_user(token)
        if user and user.user:
            return user.user.id
    except Exception:
        pass
    return None


async def require_auth(request: Request) -> str:
    """Require authentication."""
    user_id = await get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


# ============================================
# Helper: Get or Create Stripe Customer
# ============================================

async def get_or_create_stripe_customer(user_id: str) -> str:
    """Get existing Stripe customer or create new one."""
    # Check if user has Stripe customer ID
    profile = supabase.table("ci_user_profiles").select(
        "stripe_customer_id, email, full_name"
    ).eq("id", user_id).execute()

    if not profile.data:
        raise HTTPException(status_code=404, detail="User profile not found")

    user = profile.data[0]

    if user.get("stripe_customer_id"):
        return user["stripe_customer_id"]

    # Create new Stripe customer
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    customer = stripe.Customer.create(
        email=user["email"],
        name=user.get("full_name"),
        metadata={"user_id": user_id}
    )

    # Save customer ID to profile
    supabase.table("ci_user_profiles").update({
        "stripe_customer_id": customer.id
    }).eq("id", user_id).execute()

    return customer.id


# ============================================
# Checkout Endpoints
# ============================================

@router.post("/create-checkout-session")
async def create_checkout_session(
    data: CreateCheckoutSession,
    user_id: str = Depends(require_auth)
):
    """Create a Stripe Checkout session for subscription."""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured. Add STRIPE_SECRET_KEY to .env")

    # Get tier pricing
    tier = supabase.table("ci_subscription_tiers").select(
        "stripe_price_id_monthly, stripe_price_id_yearly, price_monthly, price_yearly"
    ).eq("id", data.tier_id).execute()

    if not tier.data:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {data.tier_id}")

    tier_data = tier.data[0]

    # Get price ID based on billing period
    if data.billing_period == "yearly":
        price_id = tier_data.get("stripe_price_id_yearly")
        if not price_id:
            # Create price dynamically if not configured
            price_id = f"price_{data.tier_id}_yearly"
    else:
        price_id = tier_data.get("stripe_price_id_monthly")
        if not price_id:
            price_id = f"price_{data.tier_id}_monthly"

    # Get or create customer
    customer_id = await get_or_create_stripe_customer(user_id)

    # Create checkout session
    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{
                "price": price_id,
                "quantity": 1
            }],
            success_url=data.success_url or f"{FRONTEND_URL}/settings/billing?success=true",
            cancel_url=data.cancel_url or f"{FRONTEND_URL}/settings/billing?canceled=true",
            metadata={
                "user_id": user_id,
                "tier_id": data.tier_id,
                "billing_period": data.billing_period
            }
        )

        return {"checkout_url": session.url, "session_id": session.id}

    except stripe.error.InvalidRequestError as e:
        # Price doesn't exist - return helpful error
        if "No such price" in str(e):
            return {
                "error": "Stripe prices not configured",
                "message": f"Create prices in Stripe Dashboard with IDs: price_{data.tier_id}_monthly, price_{data.tier_id}_yearly",
                "stripe_dashboard": "https://dashboard.stripe.com/prices"
            }
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-portal-session")
async def create_portal_session(
    data: CreatePortalSession,
    user_id: str = Depends(require_auth)
):
    """Create a Stripe Customer Portal session for managing subscription."""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    # Get customer ID
    profile = supabase.table("ci_user_profiles").select(
        "stripe_customer_id"
    ).eq("id", user_id).execute()

    if not profile.data or not profile.data[0].get("stripe_customer_id"):
        raise HTTPException(status_code=400, detail="No subscription found")

    customer_id = profile.data[0]["stripe_customer_id"]

    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=data.return_url or f"{FRONTEND_URL}/settings/billing"
        )

        return {"portal_url": session.url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Subscription Status
# ============================================

@router.get("/subscription", response_model=SubscriptionStatus)
async def get_subscription_status(user_id: str = Depends(require_auth)):
    """Get current subscription status."""
    try:
        profile = supabase.table("ci_user_profiles").select(
            "subscription_tier, subscription_status, stripe_subscription_id"
        ).eq("id", user_id).execute()

        if not profile.data:
            raise HTTPException(status_code=404, detail="Profile not found")

        user = profile.data[0]
        subscription_id = user.get("stripe_subscription_id")

        # Get subscription details from Stripe if available
        current_period_end = None
        cancel_at_period_end = False

        if subscription_id and STRIPE_SECRET_KEY:
            try:
                subscription = stripe.Subscription.retrieve(subscription_id)
                current_period_end = datetime.fromtimestamp(subscription.current_period_end)
                cancel_at_period_end = subscription.cancel_at_period_end
            except Exception:
                pass

        return SubscriptionStatus(
            tier=user["subscription_tier"],
            status=user["subscription_status"],
            current_period_end=current_period_end,
            cancel_at_period_end=cancel_at_period_end,
            stripe_subscription_id=subscription_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Payment History
# ============================================

@router.get("/history", response_model=list[PaymentHistoryItem])
async def get_payment_history(
    limit: int = 10,
    user_id: str = Depends(require_auth)
):
    """Get user's payment history."""
    try:
        result = supabase.table("ci_payment_history").select("*").eq(
            "user_id", user_id
        ).order("created_at", desc=True).limit(limit).execute()

        return result.data or []
    except Exception as e:
        if "PGRST205" in str(e):
            return []
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Stripe Webhook Handler
# ============================================

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature")
):
    """Handle Stripe webhook events."""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    payload = await request.body()

    # Verify webhook signature
    if STRIPE_WEBHOOK_SECRET and stripe_signature:
        try:
            event = stripe.Webhook.construct_event(
                payload, stripe_signature, STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
    else:
        # For development without webhook signing
        import json
        event = json.loads(payload)

    event_type = event.get("type") if isinstance(event, dict) else event.type
    event_id = event.get("id") if isinstance(event, dict) else event.id
    data = event.get("data", {}).get("object", {}) if isinstance(event, dict) else event.data.object

    # Log event
    try:
        supabase.table("ci_stripe_events").insert({
            "stripe_event_id": event_id,
            "event_type": event_type,
            "customer_id": data.get("customer"),
            "subscription_id": data.get("id") if "subscription" in event_type else None,
            "raw_payload": event if isinstance(event, dict) else None
        }).execute()
    except Exception:
        pass  # Don't fail webhook on logging error

    # Handle specific events
    try:
        if event_type == "checkout.session.completed":
            await handle_checkout_completed(data)

        elif event_type == "customer.subscription.created":
            await handle_subscription_created(data)

        elif event_type == "customer.subscription.updated":
            await handle_subscription_updated(data)

        elif event_type == "customer.subscription.deleted":
            await handle_subscription_deleted(data)

        elif event_type == "invoice.paid":
            await handle_invoice_paid(data)

        elif event_type == "invoice.payment_failed":
            await handle_payment_failed(data)

        # Mark event as processed
        supabase.table("ci_stripe_events").update({
            "processed": True,
            "processed_at": datetime.now().isoformat()
        }).eq("stripe_event_id", event_id).execute()

    except Exception as e:
        # Log error but return 200 to prevent Stripe retry
        supabase.table("ci_stripe_events").update({
            "error_message": str(e)
        }).eq("stripe_event_id", event_id).execute()

    return {"status": "received"}


# ============================================
# Webhook Event Handlers
# ============================================

async def handle_checkout_completed(session: dict):
    """Handle successful checkout completion."""
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")
    metadata = session.get("metadata", {})

    user_id = metadata.get("user_id")
    tier_id = metadata.get("tier_id", "pro")

    if not user_id:
        # Try to find user by customer ID
        profile = supabase.table("ci_user_profiles").select("id").eq(
            "stripe_customer_id", customer_id
        ).execute()
        if profile.data:
            user_id = profile.data[0]["id"]

    if user_id:
        # Get tier limits
        tier = supabase.table("ci_subscription_tiers").select(
            "api_calls_limit, exports_limit"
        ).eq("id", tier_id).execute()

        tier_data = tier.data[0] if tier.data else {}

        supabase.table("ci_user_profiles").update({
            "subscription_tier": tier_id,
            "subscription_status": "active",
            "stripe_subscription_id": subscription_id,
            "api_calls_limit": tier_data.get("api_calls_limit", 1000),
            "exports_limit": tier_data.get("exports_limit", 50),
            "trial_used": True,
            "updated_at": datetime.now().isoformat()
        }).eq("id", user_id).execute()


async def handle_subscription_created(subscription: dict):
    """Handle new subscription creation."""
    customer_id = subscription.get("customer")
    status = subscription.get("status")

    profile = supabase.table("ci_user_profiles").select("id").eq(
        "stripe_customer_id", customer_id
    ).execute()

    if profile.data:
        user_id = profile.data[0]["id"]
        supabase.table("ci_user_profiles").update({
            "subscription_status": status,
            "stripe_subscription_id": subscription.get("id"),
            "updated_at": datetime.now().isoformat()
        }).eq("id", user_id).execute()


async def handle_subscription_updated(subscription: dict):
    """Handle subscription updates (upgrade/downgrade/cancel)."""
    customer_id = subscription.get("customer")
    status = subscription.get("status")

    profile = supabase.table("ci_user_profiles").select("id").eq(
        "stripe_customer_id", customer_id
    ).execute()

    if profile.data:
        user_id = profile.data[0]["id"]

        update_data = {
            "subscription_status": status,
            "updated_at": datetime.now().isoformat()
        }

        # Check if downgrading to free
        if subscription.get("cancel_at_period_end"):
            # Will downgrade at end of period
            pass
        elif status == "canceled":
            update_data["subscription_tier"] = "free"
            update_data["api_calls_limit"] = 100
            update_data["exports_limit"] = 5

        supabase.table("ci_user_profiles").update(update_data).eq(
            "id", user_id
        ).execute()


async def handle_subscription_deleted(subscription: dict):
    """Handle subscription cancellation."""
    customer_id = subscription.get("customer")

    profile = supabase.table("ci_user_profiles").select("id").eq(
        "stripe_customer_id", customer_id
    ).execute()

    if profile.data:
        user_id = profile.data[0]["id"]
        supabase.table("ci_user_profiles").update({
            "subscription_tier": "free",
            "subscription_status": "canceled",
            "stripe_subscription_id": None,
            "api_calls_limit": 100,
            "exports_limit": 5,
            "updated_at": datetime.now().isoformat()
        }).eq("id", user_id).execute()


async def handle_invoice_paid(invoice: dict):
    """Handle successful payment."""
    customer_id = invoice.get("customer")

    profile = supabase.table("ci_user_profiles").select("id").eq(
        "stripe_customer_id", customer_id
    ).execute()

    if profile.data:
        user_id = profile.data[0]["id"]

        # Record payment in history
        supabase.table("ci_payment_history").insert({
            "user_id": user_id,
            "stripe_invoice_id": invoice.get("id"),
            "stripe_subscription_id": invoice.get("subscription"),
            "amount": invoice.get("amount_paid", 0),
            "currency": invoice.get("currency", "usd"),
            "status": "succeeded",
            "description": invoice.get("description"),
            "period_start": datetime.fromtimestamp(invoice.get("period_start", 0)).isoformat() if invoice.get("period_start") else None,
            "period_end": datetime.fromtimestamp(invoice.get("period_end", 0)).isoformat() if invoice.get("period_end") else None,
            "receipt_url": invoice.get("hosted_invoice_url"),
            "invoice_pdf_url": invoice.get("invoice_pdf")
        }).execute()


async def handle_payment_failed(invoice: dict):
    """Handle failed payment."""
    customer_id = invoice.get("customer")

    profile = supabase.table("ci_user_profiles").select("id").eq(
        "stripe_customer_id", customer_id
    ).execute()

    if profile.data:
        user_id = profile.data[0]["id"]

        # Update status to past_due
        supabase.table("ci_user_profiles").update({
            "subscription_status": "past_due",
            "updated_at": datetime.now().isoformat()
        }).eq("id", user_id).execute()

        # Record failed payment
        supabase.table("ci_payment_history").insert({
            "user_id": user_id,
            "stripe_invoice_id": invoice.get("id"),
            "amount": invoice.get("amount_due", 0),
            "currency": invoice.get("currency", "usd"),
            "status": "failed",
            "description": "Payment failed"
        }).execute()
