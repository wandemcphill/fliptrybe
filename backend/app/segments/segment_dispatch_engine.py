"""
=====================================================
FLIPTRYBE SEGMENT 5
DISPATCH MARKET • NEGOTIATION • OTP
ROUTING • PRICING • FRAUD LOCKS
=====================================================
Do not merge yet.
"""

from datetime import datetime, timedelta
from uuid import uuid4
import math

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, Order
from app.realtime.socket import broadcast_room_event
from app.segments.segment_notifications_engine import dispatch_notification
from app.segments.segment_payments_finance_engine import release_order_funds

# =====================================================
# MODELS
# =====================================================

class DispatchOffer(db.Model):

    __tablename__ = "dispatch_offers"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, nullable=False)
    driver_id = db.Column(db.Integer, nullable=False)

    buyer_price = db.Column(db.Float)
    driver_price = db.Column(db.Float)

    counter_count = db.Column(db.Integer, default=0)

    status = db.Column(db.String(20), default="Open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DeliveryOTP(db.Model):

    __tablename__ = "delivery_otps"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer)
    seller_otp = db.Column(db.String(6))
    buyer_otp = db.Column(db.String(6))

    seller_attempts = db.Column(db.Integer, default=0)
    buyer_attempts = db.Column(db.Integer, default=0)

    locked = db.Column(db.Boolean, default=False)


class RoutePing(db.Model):

    __tablename__ = "route_pings"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================
# PRICING ORACLE
# =====================================================

VEHICLE_MULTIPLIERS = {
    "bike": 1.0,
    "sedan": 1.8,
    "van": 2.5,
    "truck": 4.0,
}


def haversine(lat1, lon1, lat2, lon2):

    R = 6371

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(dlambda / 2) ** 2
    )

    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def guide_price(distance_km, vehicle):

    base = 350
    return round(base * distance_km * VEHICLE_MULTIPLIERS[vehicle], 2)


# =====================================================
# BLUEPRINT
# =====================================================

dispatch = Blueprint(
    "dispatch_exchange",
    __name__,
    url_prefix="/api/dispatch",
)

# =====================================================
# BROADCAST ORDER TO CITY
# =====================================================

@dispatch.route("/broadcast/<int:order_id>", methods=["POST"])
@login_required
def broadcast(order_id):

    order = Order.query.get_or_404(order_id)

    payload = {
        "type": "dispatch_offer",
        "order_id": order.id,
        "pickup": order.listing.state,
        "price": order.delivery_price if hasattr(order, "delivery_price") else None,
    }

    broadcast_room_event(f"city_{order.listing.state}", payload)

    return jsonify({"status": "broadcast"})


# =====================================================
# DRIVER BID
# =====================================================

@dispatch.route("/bid", methods=["POST"])
@login_required
def bid():

    data = request.json

    offer = DispatchOffer(
        order_id=data["order_id"],
        driver_id=current_user.id,
        buyer_price=data["buyer_price"],
        driver_price=data["driver_price"],
    )

    db.session.add(offer)
    db.session.commit()

    broadcast_room_event(
        f"order_{data['order_id']}",
        {"type": "new_bid", "price": offer.driver_price},
    )

    return jsonify({"status": "submitted"})


# =====================================================
# COUNTER OFFER
# =====================================================

@dispatch.route("/counter/<int:offer_id>", methods=["POST"])
@login_required
def counter(offer_id):

    offer = DispatchOffer.query.get_or_404(offer_id)

    if offer.counter_count >= 2:
        return jsonify({"error": "Counter limit reached"}), 400

    data = request.json
    offer.driver_price = data["driver_price"]
    offer.counter_count += 1

    db.session.commit()

    broadcast_room_event(
        f"order_{offer.order_id}",
        {"type": "counter", "price": offer.driver_price},
    )

    return jsonify({"status": "countered"})


# =====================================================
# ACCEPT BID
# =====================================================

@dispatch.route("/accept/<int:offer_id>", methods=["POST"])
@login_required
def accept(offer_id):

    offer = DispatchOffer.query.get_or_404(offer_id)

    offer.status = "Accepted"

    order = Order.query.get(offer.order_id)
    order.driver_id = offer.driver_id
    order.status = "DriverAssigned"

    otp = DeliveryOTP(
        order_id=order.id,
        seller_otp=str(uuid4().int)[:4],
        buyer_otp=str(uuid4().int)[:4],
    )

    db.session.add(otp)
    db.session.commit()

    dispatch_notification(
        order.listing.seller,
        "Pickup Code 🔐",
        f"Give this OTP to rider: {otp.seller_otp}",
        ("sms", "whatsapp"),
    )

    return jsonify({"status": "assigned"})


# =====================================================
# OTP VERIFICATION
# =====================================================

@dispatch.route("/otp/pickup", methods=["POST"])
@login_required
def pickup_otp():

    data = request.json

    otp = DeliveryOTP.query.filter_by(order_id=data["order_id"]).first()

    if otp.locked:
        return jsonify({"error": "Locked"}), 403

    if data["code"] != otp.seller_otp:
        otp.seller_attempts += 1

        if otp.seller_attempts >= 4:
            otp.locked = True

            dispatch_notification(
                otp.order.listing.seller,
                "OTP Locked ⚠️",
                "Call driver now.",
                ("sms",),
            )

        db.session.commit()
        return jsonify({"error": "Wrong"}), 400

    return jsonify({"status": "pickup_confirmed"})


@dispatch.route("/otp/dropoff", methods=["POST"])
@login_required
def dropoff_otp():

    data = request.json
    otp = DeliveryOTP.query.filter_by(order_id=data["order_id"]).first()

    if otp.locked:
        return jsonify({"error": "Locked"}), 403

    if data["code"] != otp.buyer_otp:
        otp.buyer_attempts += 1

        if otp.buyer_attempts >= 4:
            otp.locked = True

            dispatch_notification(
                otp.order.buyer,
                "OTP Locked ⚠️",
                "Track rider now.",
                ("sms",),
            )

        db.session.commit()
        return jsonify({"error": "Wrong"}), 400

    release_order_funds(Order.query.get(data["order_id"]))

    return jsonify({"status": "completed"})


# =====================================================
# ROUTE PINGS
# =====================================================

@dispatch.route("/ping", methods=["POST"])
@login_required
def ping():

    data = request.json

    ping = RoutePing(
        order_id=data["order_id"],
        lat=data["lat"],
        lng=data["lng"],
    )

    db.session.add(ping)
    db.session.commit()

    broadcast_room_event(
        f"order_{data['order_id']}",
        {"type": "route_ping", "lat": ping.lat, "lng": ping.lng},
    )

    return jsonify({"ok": True})


print("🚚 Segment 5 Loaded: Dispatch Exchange Activated")