"""
=====================================================
FLIPTRYBE SEGMENT 15
PAYMENTS • SMS • WHATSAPP • RECONCILIATION
=====================================================
Do not merge yet.
"""

import uuid
import hmac
import hashlib
from datetime import datetime

import requests
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required

from app.extensions import db
from app.models import Transaction, Withdrawal, User, Order

# =====================================================
# CONFIG
# =====================================================

PAYSTACK_BASE = "https://api.paystack.co"
TERMII_BASE = "https://api.ng.termii.com"

# =====================================================
# BLUEPRINTS
# =====================================================

payments_core = Blueprint(
    "payments_core",
    __name__,
    url_prefix="/api/payments-core",
)

admin_payments = Blueprint('admin_payments_segment_15_payouts',
    __name__,
    url_prefix="/api/admin/payments",
)

# =====================================================
# UTILS
# =====================================================

def paystack_headers():

    return {
        "Authorization": f"Bearer {current_app.config.get('PAYSTACK_SECRET_KEY')}",
        "Content-Type": "application/json",
    }


def generate_reference(prefix="FT"):

    return f"{prefix}-{uuid.uuid4().hex[:14]}"


# =====================================================
# SMS / WHATSAPP
# =====================================================

def send_sms(phone, message):

    payload = {
        "api_key": current_app.config.get("TERMII_API_KEY"),
        "to": phone,
        "from": current_app.config.get("TERMII_SENDER_ID"),
        "sms": message,
        "type": "plain",
        "channel": "generic",
    }

    try:
        requests.post(
            f"{TERMII_BASE}/api/sms/send",
            json=payload,
            timeout=10,
        )
    except Exception as e:
        current_app.logger.error(str(e))


def send_whatsapp(phone, message):

    try:
        requests.post(
            f"{TERMII_BASE}/api/whatsapp/send",
            json={
                "to": phone,
                "message": message,
            },
            timeout=10,
        )
    except Exception as e:
        current_app.logger.error(str(e))


# =====================================================
# PAYSTACK INIT
# =====================================================

def initialize_payment(user, amount):

    ref = generate_reference("ORDER")

    r = requests.post(
        f"{PAYSTACK_BASE}/transaction/initialize",
        headers=paystack_headers(),
        json={
            "email": user.email,
            "amount": int(amount * 100),
            "reference": ref,
        },
    )

    data = r.json()

    return data, ref


# =====================================================
# WEBHOOK VERIFY
# =====================================================

def verify_webhook(payload, signature):

    secret = current_app.config.get("PAYSTACK_SECRET_KEY", "")

    computed = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha512,
    ).hexdigest()

    return computed == signature


# =====================================================
# PAYSTACK CALLBACK
# =====================================================

@payments_core.route("/webhook/paystack", methods=["POST"])
def paystack_webhook():

    signature = request.headers.get("x-paystack-signature")

    if not verify_webhook(request.data, signature):
        return "invalid", 400

    payload = request.json

    event = payload.get("event")
    data = payload.get("data")

    if event == "charge.success":

        ref = data["reference"]
        amount = data["amount"] / 100

        tx = Transaction(
            amount=amount,
            type="Credit",
            reference=ref,
        )

        db.session.add(tx)
        db.session.commit()

    return "ok"


# =====================================================
# ADMIN PAYMENT SWITCH
# =====================================================

@admin_payments.route("/toggle-auto", methods=["POST"])
@login_required
def toggle_auto_payments():

    enabled = request.json.get("enabled")

    current_app.config["AUTO_PAYMENTS"] = bool(enabled)

    return jsonify({"auto_payments": enabled})


# =====================================================
# MANUAL CREDIT
# =====================================================

@admin_payments.route("/manual-credit", methods=["POST"])
@login_required
def manual_credit():

    data = request.json

    user = User.query.get_or_404(data["user_id"])
    amount = float(data["amount"])

    ref = generate_reference("MANUAL")

    user.wallet_balance += amount

    tx = Transaction(
        user_id=user.id,
        amount=amount,
        type="Credit",
        reference=ref,
    )

    db.session.add(tx)
    db.session.commit()

    send_sms(user.phone, f"FlipTrybe 💳 Wallet credited ₦{amount}. Ref: {ref}")

    return jsonify({"status": "ok", "ref": ref})


# =====================================================
# WITHDRAWALS + FEES
# =====================================================

@payments_core.route("/withdraw", methods=["POST"])
@login_required
def withdraw():

    user = current_user

    data = request.json

    amount = float(data["amount"])

    fee = 0.0

    net = amount

    if user.wallet_balance < amount:
        return jsonify({"error": "insufficient"}), 400

    user.wallet_balance -= amount

    wd = Withdrawal(
        user_id=user.id,
        amount=net,
        status="Pending",
    )

    tx = Transaction(
        user_id=user.id,
        amount=amount,
        type="Debit",
        reference=generate_reference("WD"),
    )

    db.session.add(wd)
    db.session.add(tx)
    db.session.commit()

    return jsonify({
        "status": "pending",
        "fee": fee,
        "net": net,
    })


print("💳 Segment 15 Loaded: Payments + Messaging Online")
