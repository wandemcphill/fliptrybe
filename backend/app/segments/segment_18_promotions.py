"""
=====================================================
FLIPTRYBE SEGMENT 18
COMMUNICATIONS + LIVE PAYMENTS + ADMIN CONTROL PLANE
=====================================================
Do not merge yet.
"""

import os
import hmac
import hashlib
import requests
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, Transaction, Order, Withdrawal
from app.payments.service import release_escrow


# =====================================================
# CONFIG
# =====================================================

PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET_KEY")
TERMII_KEY = os.getenv("TERMII_API_KEY")
TERMII_SENDER = os.getenv("TERMII_SENDER_ID", "FlipTrybe")

# =====================================================
# BLUEPRINTS
# =====================================================

webhooks = Blueprint("webhooks", __name__, url_prefix="/webhooks")
comms = Blueprint("comms", __name__, url_prefix="/api/comms")
admin_payments = Blueprint('admin_payments_segment_18_promotions', __name__, url_prefix="/admin/payments")


# =====================================================
# OTP ENGINE
# =====================================================

class OTPAttempt(db.Model):
    __tablename__ = "otp_attempts"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    order_id = db.Column(db.Integer)
    code = db.Column(db.String(6))
    attempts = db.Column(db.Integer, default=0)
    expires_at = db.Column(db.DateTime)


def generate_otp(order_id, user_id):
    code = str(os.urandom(3).hex())[:4]
    rec = OTPAttempt(
        order_id=order_id,
        user_id=user_id,
        code=code,
        expires_at=datetime.utcnow() + timedelta(minutes=20),
    )
    db.session.add(rec)
    db.session.commit()
    return code


def validate_otp(order_id, user_id, submitted):

    rec = OTPAttempt.query.filter_by(
        order_id=order_id,
        user_id=user_id
    ).first()

    if not rec:
        return False, "OTP not found"

    if rec.expires_at < datetime.utcnow():
        return False, "OTP expired"

    rec.attempts += 1

    if rec.attempts >= 4:
        db.session.commit()
        return False, "LOCKED"

    if rec.code != submitted:
        db.session.commit()
        return False, "INVALID"

    db.session.delete(rec)
    db.session.commit()
    return True, "OK"


# =====================================================
# TERMII SMS / WHATSAPP
# =====================================================

def send_sms(phone, message):

    url = "https://api.ng.termii.com/api/sms/send"

    payload = {
        "to": phone,
        "from": TERMII_SENDER,
        "sms": message,
        "type": "plain",
        "api_key": TERMII_KEY,
        "channel": "dnd",
    }

    requests.post(url, json=payload, timeout=10)


# =====================================================
# PAYSTACK WEBHOOK
# =====================================================

@webhooks.route("/paystack", methods=["POST"])
def paystack_hook():

    signature = request.headers.get("x-paystack-signature")

    body = request.data

    expected = hmac.new(
        PAYSTACK_SECRET.encode(),
        body,
        hashlib.sha512,
    ).hexdigest()

    if signature != expected:
        return jsonify({"error": "Invalid signature"}), 401

    payload = request.json
    event = payload.get("event")

    data = payload.get("data", {})
    ref = data.get("reference")

    if event == "charge.success":

        tx = Transaction.query.filter_by(
            reference=ref
        ).first()

        if not tx:
            tx = Transaction(
                user_id=data["metadata"]["user_id"],
                amount=data["amount"] / 100,
                type="Credit",
                reference=ref,
            )

            db.session.add(tx)
            db.session.commit()

    return jsonify({"status": "ok"})


# =====================================================
# ADMIN PAYMENT SWITCH
# =====================================================

class PaymentMode(db.Model):
    __tablename__ = "payment_modes"

    id = db.Column(db.Integer, primary_key=True)
    automatic = db.Column(db.Boolean, default=True)
    last_changed = db.Column(db.DateTime)


def get_payment_mode():

    mode = PaymentMode.query.first()

    if not mode:
        mode = PaymentMode(automatic=True)
        db.session.add(mode)
        db.session.commit()

    return mode.automatic


@admin_payments.route("/mode", methods=["GET", "POST"])
@login_required
def payment_mode():

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    mode = PaymentMode.query.first()

    if request.method == "POST":
        enabled = bool(request.json.get("automatic"))

        mode.automatic = enabled
        mode.last_changed = datetime.utcnow()

        db.session.commit()

    return jsonify({"automatic": mode.automatic})


# =====================================================
# OTP CONFIRMATION ROUTES
# =====================================================

@comms.route("/otp/confirm", methods=["POST"])
@login_required
def confirm_otp():

    data = request.json

    ok, status = validate_otp(
        order_id=data["order_id"],
        user_id=current_user.id,
        submitted=data["otp"],
    )

    if status == "LOCKED":

        send_sms(
            current_user.phone,
            "FlipTrybe: Too many OTP attempts. Contact the counterparty for the code."
        )

        return jsonify({"error": "locked"}), 403

    if not ok:
        return jsonify({"error": status}), 400

    return jsonify({"status": "confirmed"})


print("📲 Segment 18 Loaded: Messaging + Paystack + Admin Control Online")