"""
==================================================
FLIPTRYBE SEGMENT 1
PAYMENTS ENGINE + PAYSTACK + ESCROW + WEBHOOKS
==================================================
Built AFTER Genesis installer.
No duplication of existing code.
Fully merge-ready later.
"""

import os
import hmac
import hashlib
import requests
from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Order, Transaction, Withdrawal, User
from app.risk.service import run_risk_scan

# ==================================================
# DATABASE EXTENSIONS (Escrow Ledger)
# ==================================================

class EscrowLedger(db.Model):
    __tablename__ = "escrow_ledgers"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, unique=True)
    amount = db.Column(db.Float)
    status = db.Column(db.String(20), default="Held")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ==================================================
# PAYSTACK CLIENT
# ==================================================

PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET_KEY")
PAYSTACK_BASE = "https://api.paystack.co"


class PaystackClient:

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET}",
        "Content-Type": "application/json"
    }

    @staticmethod
    def initialize(email, amount, reference):
        payload = {
            "email": email,
            "amount": int(amount * 100),
            "reference": reference,
        }

        res = requests.post(
            f"{PAYSTACK_BASE}/transaction/initialize",
            json=payload,
            headers=PaystackClient.headers,
            timeout=20
        )

        return res.json()

    @staticmethod
    def verify(reference):
        res = requests.get(
            f"{PAYSTACK_BASE}/transaction/verify/{reference}",
            headers=PaystackClient.headers,
            timeout=20
        )
        return res.json()

    @staticmethod
    def create_transfer(amount, recipient):
        payload = {
            "source": "balance",
            "amount": int(amount * 100),
            "recipient": recipient
        }

        res = requests.post(
            f"{PAYSTACK_BASE}/transfer",
            json=payload,
            headers=PaystackClient.headers,
            timeout=20
        )

        return res.json()


# ==================================================
# ESCROW ENGINE
# ==================================================

def hold_escrow(order: Order, reference: str):

    ledger = EscrowLedger(
        order_id=order.id,
        amount=order.total_price,
        status="Held"
    )

    tx = Transaction(
        user_id=order.buyer_id,
        amount=order.total_price,
        type="Debit",
        reference=reference
    )

    order.status = "Escrowed"

    db.session.add_all([ledger, tx])
    db.session.commit()


# Backwards-compatible alias: some older segments import `escrow_hold`.
def escrow_hold(order: Order, reference: str):
    return hold_escrow(order, reference)


def release_escrow(order_id):

    order = Order.query.get_or_404(order_id)
    ledger = EscrowLedger.query.filter_by(order_id=order.id).first()

    if not ledger or ledger.status != "Held":
        raise RuntimeError("Escrow not active")

    risk = run_risk_scan(order)
    if risk > 0.8:
        order.listing.seller.is_frozen = True
        ledger.status = "Frozen"
        db.session.commit()
        raise RuntimeError("High risk detected, funds frozen")

    payout = order.total_price * 0.95
    seller = order.listing.seller

    seller.wallet_balance += payout
    ledger.status = "Released"
    order.status = "Completed"

    tx = Transaction(
        user_id=seller.id,
        amount=payout,
        type="Credit",
        reference=f"PAYOUT-{order.id}"
    )

    db.session.add(tx)
    db.session.commit()


# ==================================================
# WITHDRAWAL ENGINE
# ==================================================

def request_withdrawal(user: User, amount, bank, acct_no, acct_name):

    if user.wallet_balance < amount:
        raise ValueError("Insufficient funds")

    withdrawal = Withdrawal(
        user_id=user.id,
        amount=amount,
        bank_name=bank,
        account_number=acct_no,
        account_name=acct_name,
        status="Queued"
    )

    user.wallet_balance -= amount

    db.session.add(withdrawal)
    db.session.commit()

    return withdrawal


def process_withdrawal(withdrawal_id):

    withdrawal = Withdrawal.query.get(withdrawal_id)

    if not withdrawal or withdrawal.status != "Queued":
        return False

    # NOTE: Recipient creation assumed done previously
    withdrawal.status = "Processing"
    db.session.commit()

    return True


# ==================================================
# WEBHOOK VERIFICATION
# ==================================================

def verify_paystack_signature(payload, signature):

    # If PAYSTACK_SECRET is not configured (common in local/dev),
    # do not crash the server on webhook hits.
    if not PAYSTACK_SECRET:
        return False

    # If the secret isn't configured (common in local dev), fail closed.
    if not PAYSTACK_SECRET:
        return False

    computed = hmac.new(
        PAYSTACK_SECRET.encode(),
        payload,
        hashlib.sha512
    ).hexdigest()

    return hmac.compare_digest(computed, signature)


# ==================================================
# PAYMENT ROUTES
# ==================================================

payments_engine = Blueprint(
    "payments_engine",
    __name__,
    url_prefix="/api/payments-engine"
)


@payments_engine.route("/initialize/<int:order_id>")
@login_required
def initialize_payment(order_id):

    order = Order.query.get_or_404(order_id)

    ref = f"FT-{order.id}-{int(datetime.utcnow().timestamp())}"

    data = PaystackClient.initialize(
        email=current_user.email,
        amount=order.total_price,
        reference=ref
    )

    return jsonify(data)


@payments_engine.route("/withdraw", methods=["POST"])
@login_required
def withdraw():

    payload = request.json

    w = request_withdrawal(
        current_user,
        payload["amount"],
        payload["bank_name"],
        payload["account_number"],
        payload["account_name"]
    )

    return jsonify({"id": w.id, "status": w.status})


# ==================================================
# PAYSTACK WEBHOOK
# ==================================================

@payments_engine.route("/webhook", methods=["POST"])
def webhook():

    signature = request.headers.get("x-paystack-signature")
    body = request.data

    if not verify_paystack_signature(body, signature):
        return "invalid", 400

    event = request.json

    if event["event"] == "charge.success":

        ref = event["data"]["reference"]
        meta = event["data"]["metadata"] or {}
        order_id = meta.get("order_id")

        if order_id:
            order = Order.query.get(order_id)
            hold_escrow(order, ref)

    return "ok", 200


# ==================================================
# ADMIN SETTLEMENT JOB
# ==================================================

def run_settlement_cycle():

    orders = Order.query.filter_by(status="Delivered").all()

    for order in orders:
        try:
            release_escrow(order.id)
        except Exception:
            continue


print("💳 Segment 1 Loaded: Payments Engine + Escrow + Paystack")