"""
=====================================================
FLIPTRYBE SEGMENT 24
METRICS, TELEMETRY & SCALE GOVERNORS
=====================================================
Do not merge yet.
"""

from datetime import datetime, timedelta
from collections import defaultdict

from flask import Blueprint, jsonify
from flask_login import login_required, current_user

from sqlalchemy import func

from app.extensions import db
from app.models import User, Transaction, Order


# =====================================================
# BLUEPRINT
# =====================================================

metrics = Blueprint(
    "metrics",
    __name__,
    url_prefix="/admin/metrics",
)


# =====================================================
# MODELS
# =====================================================

class SystemMetric(db.Model):
    __tablename__ = "system_metrics"

    id = db.Column(db.Integer, primary_key=True)
    metric = db.Column(db.String(80))
    value = db.Column(db.Float)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)


class RevenueSnapshot(db.Model):
    __tablename__ = "revenue_snapshots"

    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Date)
    gross = db.Column(db.Float)
    fees = db.Column(db.Float)
    delivery_fees = db.Column(db.Float)


class CityThrottle(db.Model):
    __tablename__ = "city_throttles"

    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(60))
    max_orders_per_hour = db.Column(db.Integer)
    active = db.Column(db.Boolean, default=True)


# =====================================================
# METRIC RECORDING
# =====================================================

def record_metric(name, value):

    db.session.add(
        SystemMetric(
            metric=name,
            value=value,
        )
    )

    db.session.commit()


# =====================================================
# AGGREGATION
# =====================================================

def daily_revenue():

    today = datetime.utcnow().date()

    rows = db.session.query(
        func.sum(Transaction.amount)
    ).filter(
        Transaction.timestamp >= today
    ).scalar() or 0

    fees = rows * 0.15

    snap = RevenueSnapshot(
        day=today,
        gross=rows,
        fees=fees,
        delivery_fees=fees * 0.6,
    )

    db.session.add(snap)
    db.session.commit()


# =====================================================
# ROUTES
# =====================================================

@metrics.route("/system")
@login_required
def system_metrics():

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    data = SystemMetric.query.order_by(
        SystemMetric.recorded_at.desc()
    ).limit(200)

    return jsonify([
        {
            "metric": m.metric,
            "value": m.value,
            "time": m.recorded_at.isoformat(),
        }
        for m in data
    ])


@metrics.route("/revenue")
@login_required
def revenue():

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    rows = RevenueSnapshot.query.order_by(
        RevenueSnapshot.day.desc()
    )

    return jsonify([
        {
            "day": r.day.isoformat(),
            "gross": r.gross,
            "fees": r.fees,
            "delivery": r.delivery_fees,
        }
        for r in rows
    ])


# =====================================================
# CITY THROTTLING
# =====================================================

@metrics.route("/city-throttle", methods=["POST"])
@login_required
def throttle_city():

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    data = request.json

    row = CityThrottle.query.filter_by(
        city=data["city"]
    ).first()

    if not row:
        row = CityThrottle(city=data["city"])

    row.max_orders_per_hour = data["limit"]
    row.active = True

    db.session.add(row)
    db.session.commit()

    return jsonify({"status": "throttled"})


print("📊 Segment 24 Loaded: Metrics & Scaling Online")