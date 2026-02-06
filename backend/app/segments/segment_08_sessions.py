"""
=====================================================
FLIPTRYBE SEGMENT 8
COMMUNICATION ENGINE
SMS • WHATSAPP • OTP
RECEIPTS • ADMIN BLASTS
=====================================================
Do not merge yet.
"""

import os
import requests
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app.models import Notification, User
from app.extensions import db

# =====================================================
# CONFIG
# =====================================================

TERMII_API_KEY = os.getenv("TERMII_API_KEY")
TERMII_SENDER_ID = os.getenv("TERMII_SENDER_ID", "FlipTrybe")

# =====================================================
# BLUEPRINT
# =====================================================

notify = Blueprint(
    "notifications",
    __name__,
    url_prefix="/api/notify",
)

# =====================================================
# CORE SENDERS
# =====================================================

def send_sms(phone, message):

    payload = {
        "api_key": TERMII_API_KEY,
        "to": phone,
        "from": TERMII_SENDER_ID,
        "sms": message,
        "type": "plain",
        "channel": "generic",
    }

    r = requests.post(
        "https://api.ng.termii.com/api/sms/send",
        json=payload,
        timeout=10,
    )

    return r.ok


def send_whatsapp(phone, message):

    payload = {
        "api_key": TERMII_API_KEY,
        "to": phone,
        "from": "whatsapp",
        "sms": message,
        "type": "plain",
        "channel": "whatsapp",
    }

    r = requests.post(
        "https://api.ng.termii.com/api/sms/send",
        json=payload,
        timeout=10,
    )

    return r.ok


# =====================================================
# DISPATCHER
# =====================================================

def dispatch_notification(user_or_id, title, message, channels=("sms",)):

    if isinstance(user_or_id, int):
        user = User.query.get(user_or_id)
    else:
        user = user_or_id

    if not user:
        return False

    if "sms" in channels:
        send_sms(user.phone, message)

    if "whatsapp" in channels:
        send_whatsapp(user.phone, message)

    n = Notification(
        user_id=user.id,
        title=title,
        message=message,
    )

    db.session.add(n)
    db.session.commit()

    return True


# =====================================================
# ADMIN BROADCAST
# =====================================================

@notify.route("/admin/broadcast", methods=["POST"])
@login_required
def admin_broadcast():

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    data = request.json

    users = User.query.all()

    for u in users:
        dispatch_notification(
            u,
            data["title"],
            data["message"],
            ("sms", "whatsapp"),
        )

    return jsonify({"status": "sent"})


# =====================================================
# RIDE RECEIPTS
# =====================================================

def send_ride_receipt(user, driver, pickup, dropoff, amount):

    msg = (
        f"🚕 FlipTrybe Ride Confirmed\n"
        f"Driver: {driver.name}\n"
        f"Phone: {driver.phone}\n"
        f"Vehicle: {driver.vehicle_type}\n"
        f"Plate: {driver.vehicle_plate}\n\n"
        f"Pickup: {pickup}\n"
        f"Dropoff: {dropoff}\n"
        f"Paid: ₦{amount}\n\n"
        "Thanks for riding FlipTrybe 💛"
    )

    dispatch_notification(
        user,
        "Ride Receipt 🚕",
        msg,
        ("sms", "whatsapp"),
    )


print("📡 Segment 8 Loaded: Messaging Online")