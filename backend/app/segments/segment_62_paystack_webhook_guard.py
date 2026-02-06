"""
=====================================================
FLIPTRYBE SEGMENT 62
PAYSTACK WEBHOOK GUARD
=====================================================
Verifies webhook signatures,
prevents replay,
deduplicates events,
routes to escrow engine.
=====================================================
"""

import hmac
import hashlib
import time
import json
from datetime import datetime
from typing import Dict, Set

# =====================================================
# CONFIG
# =====================================================

PAYSTACK_SECRET = "ENV_PAYSTACK_SECRET"
MAX_SKEW_SECONDS = 300


# =====================================================
# STORES (STUB)
# =====================================================

PROCESSED_EVENTS: Set[str] = set()
RECEIPTS: Dict[str, dict] = {}


# =====================================================
# SIGNATURE VERIFICATION
# =====================================================

def verify_signature(raw_body: bytes, signature: str) -> bool:

    digest = hmac.new(
        PAYSTACK_SECRET.encode(),
        raw_body,
        hashlib.sha512
    ).hexdigest()

    return hmac.compare_digest(digest, signature)


# =====================================================
# REPLAY DEFENSE
# =====================================================

def within_time_window(timestamp: int) -> bool:

    now = int(time.time())
    return abs(now - timestamp) <= MAX_SKEW_SECONDS


# =====================================================
# IDEMPOTENCY
# =====================================================

def is_duplicate(event_id: str) -> bool:
    return event_id in PROCESSED_EVENTS


def mark_processed(event_id: str):
    PROCESSED_EVENTS.add(event_id)


# =====================================================
# RECEIPT CAPTURE
# =====================================================

def store_receipt(event_id: str, payload: dict):

    RECEIPTS[event_id] = {
        "payload": payload,
        "stored_at": datetime.utcnow()
    }


# =====================================================
# EVENT ROUTER
# =====================================================

def handle_paystack_event(headers: dict, raw_body: bytes):

    signature = headers.get("x-paystack-signature")
    if not signature:
        return False, "Missing signature"

    if not verify_signature(raw_body, signature):
        return False, "Invalid signature"

    payload = json.loads(raw_body.decode())

    event_id = payload.get("id") or payload.get("event")
    timestamp = payload.get("created_at") or int(time.time())

    if not within_time_window(int(timestamp)):
        return False, "Replay detected"

    if is_duplicate(event_id):
        return True, "Duplicate ignored"

    mark_processed(event_id)
    store_receipt(event_id, payload)

    route_event(payload)

    return True, "Processed"


# =====================================================
# ESCROW PIPELINE
# =====================================================

def route_event(payload: dict):

    event_type = payload.get("event")

    if event_type == "charge.success":
        on_payment_success(payload)

    elif event_type == "transfer.success":
        on_payout_success(payload)

    elif event_type == "charge.failed":
        on_payment_failed(payload)


# =====================================================
# EVENT HANDLERS
# =====================================================

def on_payment_success(payload):

    data = payload.get("data", {})
    order_ref = data.get("reference")

    print(f"💰 Payment confirmed for {order_ref}")


def on_payout_success(payload):

    data = payload.get("data", {})
    transfer_ref = data.get("reference")

    print(f"🏦 Payout completed {transfer_ref}")


def on_payment_failed(payload):

    data = payload.get("data", {})
    ref = data.get("reference")

    print(f"❌ Payment failed {ref}")


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    fake_payload = {
        "id": "evt_123",
        "event": "charge.success",
        "created_at": int(time.time()),
        "data": {"reference": "ORD-55"}
    }

    raw = json.dumps(fake_payload).encode()

    sig = hmac.new(
        PAYSTACK_SECRET.encode(),
        raw,
        hashlib.sha512
    ).hexdigest()

    print(handle_paystack_event(
        {"x-paystack-signature": sig},
        raw
    ))