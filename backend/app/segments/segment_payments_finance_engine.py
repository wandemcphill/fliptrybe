"""
==================================================
FLIPTRYBE SEGMENT 4
PAYMENTS • PAYSTACK • ESCROW • LEDGER
RECONCILIATION • ADMIN OVERRIDES
==================================================
Do not merge yet.
"""

import os
import hmac
import hashlib
from datetime import datetime
from uuid import uuid4

import requests
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models import (
    User,
    Order,
    Transaction,
    Withdrawal,
)

from app.risk.service import run_risk_scan
from app.segments.segment_notifications_engine import (
    dispatch_notification,
    risk_freeze,
)

# ==================================================
# GLOBAL ADMIN PAYMENT CONTROL
# ==================================================

class PaymentSwitch(db.Model):
    __tablename__ = "payment_switch"

    id = db.Column(db.Integer, primary_key=True)
    auto_payout_enabled = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def status():
        row = PaymentSwitch.query.first()
        if not row:
            row = PaymentSwitch()
            db.session.add(row)
            db.session.commit()
        return row


# ==================================================
# PAYSTACK WRAPPER
# ==================================================

class PaystackGateway:

    BASE = "https://api.paystack.co"

    def __init__(self):
        self.secret = os.getenv("PAYSTACK_SECRET_KEY")

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.secret}",
            "Content-Type": "application/json",
        }

    def verify(self, reference):
        r = requests.get(
            f"{self.BASE}/transaction/verify/{reference}",
            headers=self._headers(),
            timeout=30,
        )
        return r.json()

    def initialize(self, email, amount, reference):
        r = requests.post(
            f"{self.BASE}/transaction/initialize",
            headers=self._headers(),
            json={
                "email": email,
                "amount": int(amount * 100),
                "reference": reference,
            },
            timeout=30,
        )
        return r.json()


paystack = PaystackGateway()

# ==================================================
# WEBHOOK VERIFIER
# ==================================================

def verify_paystack_signature(body, signature):
    secret = os.getenv("PAYSTACK_SECRET_KEY", "")
    computed = hmac.new(
        secret.encode(),
        body,
        hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(computed, signature)


# ==================================================
# FINANCE BLUEPRINT
# ==================================================

finance = Blueprint('finance_segment_payments_finance_engine',
    __name__,
    url_prefix="/api/finance"
)

# ==================================================
# PAYSTACK WEBHOOK RECEIVER
# ==================================================

@finance.route("/webhooks/paystack", methods=["POST"])
def paystack_webhook():

    sig = request.headers.get("x-paystack-signature")

    if not verify_paystack_signature(request.data, sig):
        return "Invalid signature", 400

    payload = request.json
    event = payload.get("event")

    data = payload.get("data", {})
    reference = data.get("reference")

    tx = Transaction.query.filter_by(reference=reference).first()

    if event == "charge.success" and tx:

        tx.type = "Credit"
        user = tx.user
        user.wallet_balance += tx.amount

        db.session.commit()

        dispatch_notification(
            user=user,
            title="Wallet Funded 💰",
            message=f"₦{tx.amount:,.0f} added to your wallet.",
            channels=("app", "sms"),
        )

    return "ok", 200


# ==================================================
# WALLET FUNDING
# ==================================================

@finance.route("/wallet/fund", methods=["POST"])
@login_required
def fund_wallet():

    data = request.json
    amount = float(data["amount"])

    ref = f"WAL-{uuid4().hex[:10]}"

    tx = Transaction(
        user_id=current_user.id,
        amount=amount,
        type="Pending",
        reference=ref,
    )

    db.session.add(tx)
    db.session.commit()

    resp = paystack.initialize(
        current_user.email,
        amount,
        ref,
    )

    return jsonify(resp)


# ==================================================
# ESCROW HOLD
# ==================================================

def hold_escrow(order: Order):

    risk = run_risk_scan(order)

    if risk > 0.85:
        order.listing.seller.is_frozen = True
        db.session.commit()
        risk_freeze(order.listing.seller)
        raise RuntimeError("Transaction blocked")

    order.status = "Escrowed"
    db.session.commit()


# ==================================================
# RELEASE FUNDS
# ==================================================

def release_order_funds(order: Order):

    switch = PaymentSwitch.status()

    if not switch.auto_payout_enabled:
        order.status = "ManualReview"
        db.session.commit()
        return "manual"

    seller = order.listing.seller

    amount = order.total_price * 0.85  # FlipTrybe 15%

    seller.wallet_balance += amount

    tx = Transaction(
        user_id=seller.id,
        amount=amount,
        type="Credit",
        reference=f"SALE-{order.id}",
    )

    db.session.add(tx)

    order.status = "Completed"
    db.session.commit()

    dispatch_notification(
        user=seller,
        title="Sale Completed 🎉",
        message=f"₦{amount:,.0f} credited.",
        channels=("app", "sms"),
    )

    return "auto"


# ==================================================
# ADMIN TOGGLE PAYOUT MODE
# ==================================================

@finance.route("/admin/toggle-payout", methods=["POST"])
@login_required
def toggle_payout():

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    switch = PaymentSwitch.status()
    switch.auto_payout_enabled = not switch.auto_payout_enabled

    db.session.commit()

    return jsonify({
        "auto": switch.auto_payout_enabled
    })


# ==================================================
# WITHDRAWALS
# ==================================================

@finance.route("/wallet/withdraw", methods=["POST"])
@login_required
def withdraw():

    data = request.json
    amount = float(data["amount"])

    fee = round(amount * 0.02, 2)
    total = amount + fee

    if current_user.wallet_balance < total:
        return jsonify({"error": "Insufficient balance"}), 400

    w = Withdrawal(
        user_id=current_user.id,
        amount=amount,
        bank_name=data["bank_name"],
        account_number=data["account_number"],
        account_name=data["account_name"],
    )

    current_user.wallet_balance -= total

    tx = Transaction(
        user_id=current_user.id,
        amount=amount,
        type="Debit",
        reference=f"WDR-{uuid4().hex[:8]}",
    )

    db.session.add_all([w, tx])
    db.session.commit()

    return jsonify({
        "status": "pending",
        "fee": fee,
    })


# ==================================================
# ADMIN FINANCE DASHBOARD
# ==================================================

@finance.route("/admin/summary")
@login_required
def finance_summary():

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    total_wallets = db.session.query(
        db.func.sum(User.wallet_balance)
    ).scalar() or 0

    total_withdrawals = db.session.query(
        db.func.sum(Withdrawal.amount)
    ).scalar() or 0

    total_volume = db.session.query(
        db.func.sum(Transaction.amount)
    ).scalar() or 0

    return jsonify({
        "wallets": total_wallets,
        "withdrawals": total_withdrawals,
        "volume": total_volume,
    })


print("💳 Segment 4 Loaded: Finance Grid Active")