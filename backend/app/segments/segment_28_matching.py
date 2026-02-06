"""
=====================================================
FLIPTRYBE SEGMENT 28
RIDE HAILING & DISPATCH MARKETPLACE
=====================================================
Do not merge yet.
"""

import uuid
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required

from app.extensions import db
from app.models import User
from app.realtime.socket import broadcast_room_event
from app.payments.service import release_escrow
from app.workers.utils import utcnow

from app.segments.segment_live_payments_and_comms import initialize_payment, send_sms


# =====================================================
# BLUEPRINT
# =====================================================

ride = Blueprint(
    "ride",
    __name__,
    url_prefix="/api/ride",
)


# =====================================================
# MODELS
# =====================================================

class RideRequest(db.Model):
    __tablename__ = "ride_requests"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True)

    phone = db.Column(db.String(25))
    pickup = db.Column(db.String(200))
    dropoff = db.Column(db.String(200))

    amount = db.Column(db.Float)

    vehicle_type = db.Column(db.String(20))

    status = db.Column(db.String(20), default="Pending")

    driver_id = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================
# CREATE REQUEST
# =====================================================

@ride.route("/request", methods=["POST"])
def create_ride():

    data = request.json

    ref = str(uuid.uuid4())

    ride_req = RideRequest(
        reference=ref,
        phone=data["phone"],
        pickup=data["pickup"],
        dropoff=data["dropoff"],
        amount=data["amount"],
        vehicle_type=data["vehicle_type"],
    )

    db.session.add(ride_req)
    db.session.commit()

    paystack = initialize_payment(
        data["amount"],
        data["email"],
        ref,
    )

    return jsonify({
        "reference": ref,
        "payment_url": paystack["data"]["authorization_url"],
    })


# =====================================================
# DRIVER ACCEPT
# =====================================================

@ride.route("/accept/<reference>", methods=["POST"])
@login_required
def accept_ride(reference):

    ride_req = RideRequest.query.filter_by(
        reference=reference
    ).first_or_404()

    ride_req.driver_id = current_user.id
    ride_req.status = "Accepted"

    db.session.commit()

    send_sms(
        ride_req.phone,
        f"🚕 FlipTrybe Ride Confirmed\nDriver: {current_user.name}\nPlate: TBD\nPickup: {ride_req.pickup}",
    )

    return jsonify({"status": "assigned"})


print("🚕 Segment 28 Loaded: Ride Hailing Online")