"""
=====================================================
FLIPTRYBE SEGMENT 14
AI DISPATCH • ROUTE OPTIMIZATION • ETA • SURGE
=====================================================
Do not merge yet.
"""

from datetime import datetime
import math
import uuid

from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.extensions import db
from app.models import Order, User

# =====================================================
# BLUEPRINT
# =====================================================

dispatch_ai = Blueprint(
    "dispatch_ai",
    __name__,
    url_prefix="/api/dispatch",
)

# =====================================================
# GEO HELPERS
# =====================================================

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

    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


# =====================================================
# SURGE PRICING
# =====================================================

def surge_multiplier(active_orders, drivers_available):

    if drivers_available == 0:
        return 3.0

    ratio = active_orders / drivers_available

    if ratio < 1:
        return 1.0
    if ratio < 2:
        return 1.3
    if ratio < 3:
        return 1.6
    return 2.0


# =====================================================
# DRIVER MATCHING ENGINE
# =====================================================

def match_driver(order, pickup):

    drivers = User.query.filter_by(is_driver=True, is_frozen=False).all()

    best_driver = None
    best_score = float("inf")

    for d in drivers:

        if not hasattr(d, "lat") or not hasattr(d, "lng"):
            continue

        distance = haversine(
            pickup["lat"],
            pickup["lng"],
            d.lat,
            d.lng,
        )

        score = distance - d.pilot_score

        if score < best_score:
            best_score = score
            best_driver = d

    return best_driver


# =====================================================
# ETA CALCULATION
# =====================================================

def estimate_eta_km(distance_km):

    avg_speed = 35
    hours = distance_km / avg_speed

    return int(hours * 60)


# =====================================================
# DISPATCH ENDPOINT
# =====================================================

@dispatch_ai.route("/assign/<int:order_id>", methods=["POST"])
@login_required
def assign_driver(order_id):

    order = Order.query.get_or_404(order_id)

    payload = request.json or {}

    pickup = payload.get("pickup")

    if not pickup:
        return jsonify({"error": "pickup missing"}), 400

    active_orders = Order.query.filter_by(status="Escrowed").count()
    drivers = User.query.filter_by(is_driver=True).count()

    surge = surge_multiplier(active_orders, drivers)

    driver = match_driver(order, pickup)

    if not driver:
        return jsonify({"error": "no drivers available"}), 404

    order.driver_id = driver.id
    order.status = "Assigned"
    order.total_price *= surge

    db.session.commit()

    distance = haversine(
        pickup["lat"],
        pickup["lng"],
        driver.lat,
        driver.lng,
    )

    eta = estimate_eta_km(distance)

    return jsonify({
        "order_id": order.id,
        "driver_id": driver.id,
        "surge": surge,
        "eta_minutes": eta,
    })


print("🚦 Segment 14 Loaded: Dispatch AI Online")