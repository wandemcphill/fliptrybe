"""
=====================================================
FLIPTRYBE SEGMENT 26
LIVE PAYMENTS & COMMUNICATIONS
=====================================================
Do not merge yet.
"""

import uuid
import hashlib
import hmac
import os
import requests
from datetime import datetime

from flask import Blueprint, request, jsonify, abort

from app.extensions import db
from app.models import Transaction, Order, User
from app.payments.service import release_escrow


# =====================================================
# CONFIG
# =====================================================

PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET_KEY", "")
TERMII_KEY = os.getenv("TERMII_API_KEY")
TERMII_SENDER = os.getenv("TERMII_SENDER_ID", "FlipTrybe")

PAYSTACK_BASE = "https://api.paystack.co"
TERMII_BASE = "https://api.ng.termii.com/api"


# =====================================================
# BLUEPRINT
# =====================================================

live_payments = Blueprint(
    "live_payments",
    __name__,
    url_prefix="/api/live",
)


# =====================================================
# IDP KEY
# =====================================================

def generate_idempotency_key():
    return str(uuid.uuid4())


# =====================================================
# SMS / WHATSAPP
# =====================================================

def send_sms(phone, message, channel='generic'):

    # Non-fatal: if TERMII isn't configured, we simply don't send.
    from app.utils.termii_client import send_termii_message

    ok, _detail = send_termii_message(channel=channel, to=phone, message=message)
    return ok


# =====================================================
# PAYSTACK CHARGE
# =====================================================

def initialize_payment(amount, email, reference):

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET}",
        "Content-Type": "application/json",
    }

    data = {
        "email": email,
        "amount": int(amount * 100),
        "reference": reference,
    }

    res = requests.post(
        f"{PAYSTACK_BASE}/transaction/initialize",
        json=data,
        headers=headers,
        timeout=10,
    )

    return res.json()


# =====================================================
# WEBHOOK VERIFY
# =====================================================

def verify_paystack_signature(payload, signature):

    if not PAYSTACK_SECRET or not signature:
        return False

    digest = hmac.new(
        PAYSTACK_SECRET.encode(),
        payload,
        hashlib.sha512,
    ).hexdigest()

    return hmac.compare_digest(digest, signature)


# =====================================================
# WEBHOOK RECEIVER
# =====================================================

@live_payments.route("/webhook/paystack", methods=["POST"])
def paystack_webhook():

    signature = request.headers.get("x-paystack-signature")

    if not verify_paystack_signature(
        request.data,
        signature,
    ):
        abort(401)

    event = request.json

    if event["event"] == "charge.success":

        data = event["data"]
        reference = data["reference"]
        amount = data["amount"] / 100

        tx = Transaction.query.filter_by(
            reference=reference
        ).first()

        if not tx:

            tx = Transaction(
                amount=amount,
                type="Credit",
                reference=reference,
            )

            db.session.add(tx)

        db.session.commit()

    return jsonify({"status": "ok"})


# =====================================================
# ESCROW SYNC
# =====================================================

@live_payments.route("/release-escrow/<int:order_id>", methods=["POST"])
def release_order(order_id):

    try:
        release_escrow(order_id)
        return jsonify({"released": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


print("💳 Segment 26 Loaded: Live Payments & Messaging Online")