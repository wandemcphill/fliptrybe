"""
=====================================================
FLIPTRYBE SEGMENT 29
DELIVERY SECURITY & FRAUD PREVENTION
=====================================================
Do not merge yet.
"""

import random
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Order, User
from app.realtime.socket import broadcast_room_event

from app.segments.segment_live_payments_and_comms import send_sms


# =====================================================
# BLUEPRINT
# =====================================================

delivery_security = Blueprint(
    "delivery_security",
    __name__,
    url_prefix="/api/security",
)


# =====================================================
# MODELS
# =====================================================

class OTPAttempt(db.Model):
    __tablename__ = "otp_attempts"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer)

    role = db.Column(db.String(20))  # buyer/seller/driver
    otp = db.Column(db.String(6))

    attempts = db.Column(db.Integer, default=0)
    locked = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================
# OTP GENERATION
# =====================================================

def generate_otp():
    return str(random.randint(1000, 9999))


# =====================================================
# ROUTE DEVIATION
# =====================================================

def trigger_route_alert(order_id, reason):

    broadcast_room_event(
        f"order_{order_id}",
        {
            "type": "route_alert",
            "order_id": order_id,
            "reason": reason,
        },
    )


# =====================================================
# OTP ISSUE
# =====================================================

def issue_otp(order_id, user, role):

    otp = generate_otp()

    rec = OTPAttempt(
        order_id=order_id,
        role=role,
        otp=otp,
    )

    db.session.add(rec)
    db.session.commit()

    send_sms(
        user.phone,
        f"🔐 FlipTrybe OTP: {otp}\nGive to dispatch to release funds.",
    )


# =====================================================
# OTP VERIFY
# =====================================================

@delivery_security.route("/verify-otp", methods=["POST"])
@login_required
def verify_otp():

    data = request.json

    rec = OTPAttempt.query.filter_by(
        order_id=data["order_id"],
        role=data["role"],
        locked=False,
    ).first_or_404()

    if rec.otp != data["otp"]:
        rec.attempts += 1

        if rec.attempts >= 4:
            rec.locked = True

            trigger_route_alert(
                rec.order_id,
                "OTP locked after failures",
            )

        db.session.commit()
        return jsonify({"error": "invalid"}), 400

    db.session.delete(rec)
    db.session.commit()

    return jsonify({"status": "verified"})


print("🔐 Segment 29 Loaded: Delivery Security Online")