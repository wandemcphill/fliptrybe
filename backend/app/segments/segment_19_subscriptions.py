"""
=====================================================
FLIPTRYBE SEGMENT 19
LOGISTICS + RIDES + DISPATCH NEGOTIATION ENGINE
=====================================================
Do not merge yet.
"""

from datetime import datetime, timedelta
import math

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, Order
from app.realtime.socket import broadcast_room_event
from app.comms_and_payments_live import send_sms   # merged later


# =====================================================
# BLUEPRINTS
# =====================================================

rides = Blueprint("rides", __name__, url_prefix="/api/rides")
dispatch_market = Blueprint("dispatch_market", __name__, url_prefix="/api/dispatch")


# =====================================================
# MODELS
# =====================================================

class RideRequest(db.Model):
    __tablename__ = "ride_requests"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    rider_phone = db.Column(db.String(30))
    pickup_lat = db.Column(db.Float)
    pickup_lng = db.Column(db.Float)
    drop_lat = db.Column(db.Float)
    drop_lng = db.Column(db.Float)

    vehicle_type = db.Column(db.String(20))
    offered_price = db.Column(db.Float)

    status = db.Column(db.String(20), default="open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DispatchOffer(db.Model):
    __tablename__ = "dispatch_offers"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer)
    driver_id = db.Column(db.Integer)
    counter_price = db.Column(db.Float)
    round_number = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class RouteDeviation(db.Model):
    __tablename__ = "route_deviations"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================
# PRICE GUIDANCE ENGINE
# =====================================================

BASE_RATES = {
    "bike": 120,
    "sedan": 200,
    "van": 350,
    "truck": 600,
}


def haversine(lat1, lng1, lat2, lng2):

    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )

    return 2 * R * math.asin(math.sqrt(a))


def price_guidance(vehicle, km):

    base = BASE_RATES.get(vehicle, 200)
    minimum = km * base

    return round(minimum * 1.15, 2)  # invisible floor +15%


# =====================================================
# RIDE CREATION (NO KYC)
# =====================================================

@rides.route("/request", methods=["POST"])
def request_ride():

    data = request.json

    km = haversine(
        data["pickup_lat"],
        data["pickup_lng"],
        data["drop_lat"],
        data["drop_lng"],
    )

    guide = price_guidance(data["vehicle_type"], km)

    ride = RideRequest(
        rider_phone=data["phone"],
        pickup_lat=data["pickup_lat"],
        pickup_lng=data["pickup_lng"],
        drop_lat=data["drop_lat"],
        drop_lng=data["drop_lng"],
        vehicle_type=data["vehicle_type"],
        offered_price=data["offer"],
    )

    db.session.add(ride)
    db.session.commit()

    return jsonify({
        "ride_id": ride.id,
        "suggested_minimum": guide,
    })


# =====================================================
# DISPATCH BOARD
# =====================================================

@dispatch_market.route("/open")
@login_required
def open_rides():

    rides = RideRequest.query.filter_by(status="open").all()

    return jsonify([
        {
            "id": r.id,
            "vehicle": r.vehicle_type,
            "offer": r.offered_price,
            "pickup": [r.pickup_lat, r.pickup_lng],
            "drop": [r.drop_lat, r.drop_lng],
        }
        for r in rides
    ])


@dispatch_market.route("/offer", methods=["POST"])
@login_required
def submit_offer():

    data = request.json

    offer = DispatchOffer(
        ride_id=data["ride_id"],
        driver_id=current_user.id,
        counter_price=data["price"],
        round_number=data.get("round", 1),
    )

    db.session.add(offer)
    db.session.commit()

    return jsonify({"status": "submitted"})


# =====================================================
# ROUTE MONITORING
# =====================================================

def detect_route_deviation(order_id, lat, lng, target_lat, target_lng):

    dist = haversine(lat, lng, target_lat, target_lng)

    if dist > 5:  # km off-route

        dev = RouteDeviation(
            order_id=order_id,
            lat=lat,
            lng=lng,
        )

        db.session.add(dev)
        db.session.commit()

        broadcast_room_event(
            f"order_{order_id}",
            {
                "type": "route_alert",
                "lat": lat,
                "lng": lng,
            },
        )


print("🚕 Segment 19 Loaded: Logistics & Ride Hailing Online")