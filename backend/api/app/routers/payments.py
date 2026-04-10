"""
payments.py — Dodo Payments integration for ShortClipr subscriptions.

Plan tiers and their credit allocations:
  free     → 3 shorts/month (no payment)
  pro_50   → 50  shorts/month  @ $10
  pro_100  → 100 shorts/month  @ $19
  pro_200  → 200 shorts/month  @ $30
  pro_400  → 400 shorts/month  @ $49
  pro_500  → 500 shorts/month  @ $57

Endpoints:
  POST /payments/checkout   → create Dodo checkout session, return redirect URL
  POST /payments/webhook    → receive Dodo webhook, update user tier + credits
  GET  /payments/plans      → enumerate all plan tiers (used by frontend)
"""
import hashlib
import hmac
import json
import logging
import os
from typing import Optional

import dodopayments
from dodopayments import DodoPayments
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel

from app.middleware.auth import get_current_user
from app.models.user import UserDB
from app.services.database import get_user_by_id, update_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])

# ─────────────────────────────────────────────────────────────────────────────
# Dodo client (lazy init)
# ─────────────────────────────────────────────────────────────────────────────
_dodo: Optional[DodoPayments] = None

def _get_dodo() -> DodoPayments:
    global _dodo
    if _dodo is None:
        env = os.getenv("DODO_ENV", "test_mode")   # "live_mode" in production
        _dodo = DodoPayments(
            bearer_token=os.getenv("DODO_PAYMENTS_API_KEY"),
            environment=env,
        )
    return _dodo


# ─────────────────────────────────────────────────────────────────────────────
# Plan catalog — single source of truth for pricing + credit limits
# ─────────────────────────────────────────────────────────────────────────────
PLANS: dict[str, dict] = {
    "free": {
        "tier":          "free",
        "label":         "Free",
        "credits_limit": 3,
        "price_usd":     0,
        "dodo_product_id": None,   # no payment required
    },
    "pro_50": {
        "tier":          "pro_50",
        "label":         "Pro · 50 Shorts",
        "credits_limit": 50,
        "price_usd":     10,
        "dodo_product_id": os.getenv("DODO_PRODUCT_PRO_50",  "prod_pro_50"),
    },
    "pro_100": {
        "tier":          "pro_100",
        "label":         "Pro · 100 Shorts",
        "credits_limit": 100,
        "price_usd":     19,
        "dodo_product_id": os.getenv("DODO_PRODUCT_PRO_100", "prod_pro_100"),
    },
    "pro_200": {
        "tier":          "pro_200",
        "label":         "Pro · 200 Shorts",
        "credits_limit": 200,
        "price_usd":     30,
        "dodo_product_id": os.getenv("DODO_PRODUCT_PRO_200", "prod_pro_200"),
    },
    "pro_400": {
        "tier":          "pro_400",
        "label":         "Pro · 400 Shorts",
        "credits_limit": 400,
        "price_usd":     49,
        "dodo_product_id": os.getenv("DODO_PRODUCT_PRO_400", "prod_pro_400"),
    },
    "pro_500": {
        "tier":          "pro_500",
        "label":         "Pro · 500 Shorts",
        "credits_limit": 500,
        "price_usd":     57,
        "dodo_product_id": os.getenv("DODO_PRODUCT_PRO_500", "prod_pro_500"),
    },
}

# Map Dodo product_id → plan key for webhook resolution
_PRODUCT_TO_PLAN: dict[str, str] = {
    v["dodo_product_id"]: k
    for k, v in PLANS.items()
    if v["dodo_product_id"]
}


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response schemas
# ─────────────────────────────────────────────────────────────────────────────
class CheckoutRequest(BaseModel):
    tier: str           # one of the PLANS keys e.g. "pro_50"
    success_url: str    # frontend redirect after payment
    cancel_url:  str


class CheckoutResponse(BaseModel):
    checkout_url: str
    tier: str
    price_usd: int
    credits_limit: int


# ─────────────────────────────────────────────────────────────────────────────
# GET /payments/plans — list all plans (used by frontend pricing section)
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/plans", summary="List all available subscription plans")
async def list_plans():
    return [
        {
            "tier":          p["tier"],
            "label":         p["label"],
            "credits_limit": p["credits_limit"],
            "price_usd":     p["price_usd"],
        }
        for p in PLANS.values()
    ]


# ─────────────────────────────────────────────────────────────────────────────
# POST /payments/checkout — create a Dodo checkout session
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/checkout", response_model=CheckoutResponse, summary="Create a checkout session")
async def create_checkout(
    body: CheckoutRequest,
    current_user: UserDB = Depends(get_current_user),
):
    plan = PLANS.get(body.tier)
    if not plan:
        raise HTTPException(status_code=400, detail=f"Unknown plan tier: '{body.tier}'")
    if plan["dodo_product_id"] is None:
        raise HTTPException(status_code=400, detail="Free tier requires no payment.")

    dodo = _get_dodo()
    try:
        session = dodo.checkout_sessions.create(
            product_cart=[{"product_id": plan["dodo_product_id"], "quantity": 1}],
            customer={
                "email": current_user.email,
                "name":  current_user.name,
            },
            metadata={
                "user_id": current_user.id,
                "tier":    body.tier,
            },
            return_url=body.success_url,
        )
    except Exception as exc:
        logger.error(f"Dodo checkout creation failed: {exc}")
        raise HTTPException(status_code=502, detail="Payment provider error. Please try again.")

    return CheckoutResponse(
        checkout_url=session.checkout_url,
        tier=body.tier,
        price_usd=plan["price_usd"],
        credits_limit=plan["credits_limit"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /payments/webhook — Dodo webhook handler
# ─────────────────────────────────────────────────────────────────────────────
WEBHOOK_SECRET = os.getenv("DODO_WEBHOOK_SECRET", "")


def _verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify HMAC-SHA256 signature from Dodo Payments webhook header."""
    if not WEBHOOK_SECRET:
        logger.warning("DODO_WEBHOOK_SECRET not set — skipping signature verification")
        return True
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def _apply_plan_to_user(user_id: str, tier: str) -> None:
    """Upgrade a user's subscription tier and reset their credit limit."""
    plan = PLANS.get(tier)
    if not plan:
        logger.error(f"Webhook: Unknown tier '{tier}' for user {user_id}")
        return

    await update_user(user_id, {
        "subscription_tier": tier,
        "credits_limit":     plan["credits_limit"],
        "credits_used":      0,    # reset usage on new billing cycle
    })
    logger.info(f"User {user_id} upgraded to tier '{tier}' ({plan['credits_limit']} credits/month)")


@router.post("/webhook", summary="Dodo Payments webhook receiver")
async def dodo_webhook(
    request: Request,
    webhook_signature: str = Header(default="", alias="webhook-signature"),
):
    payload = await request.body()

    if not _verify_webhook_signature(payload, webhook_signature):
        logger.warning("Webhook signature mismatch — rejecting.")
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")

    try:
        event = json.loads(payload)
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed JSON payload.")

    event_type = event.get("type", "")
    data       = event.get("data", {})
    metadata   = data.get("metadata", {})
    user_id    = metadata.get("user_id")
    tier       = metadata.get("tier")

    logger.info(f"Dodo webhook: event='{event_type}' user={user_id} tier={tier}")

    # subscription.active — new subscription created and paid
    if event_type == "subscription.active":
        if user_id and tier:
            await _apply_plan_to_user(user_id, tier)

    # payment.succeeded — one-time or recurring payment success
    elif event_type == "payment.succeeded":
        product_id = data.get("product_id") or (
            data.get("product_cart", [{}])[0].get("product_id")
        )
        resolved_tier = tier or _PRODUCT_TO_PLAN.get(product_id)
        if user_id and resolved_tier:
            await _apply_plan_to_user(user_id, resolved_tier)

    # subscription.renewed — monthly charge successful, reset credits
    elif event_type == "subscription.renewed":
        if user_id:
            user = await get_user_by_id(user_id)
            if user:
                plan = PLANS.get(user.subscription_tier)
                if plan:
                    await update_user(user_id, {
                        "credits_used": 0,   # reset monthly quota
                    })
                    logger.info(f"User {user_id} credits reset for renewal.")

    # subscription.on_hold / subscription.cancelled — downgrade to free
    elif event_type in ("subscription.on_hold", "subscription.cancelled"):
        if user_id:
            await _apply_plan_to_user(user_id, "free")

    return {"received": True}
