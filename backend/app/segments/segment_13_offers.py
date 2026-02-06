"""
=====================================================
FLIPTRYBE SEGMENT 13
ANALYTICS • ML RISK • REGULATORY EXPORT GRID
BI Dashboards • Fraud Models • Tax Reports
=====================================================
Do not merge yet.
"""

from datetime import datetime, timedelta
import csv
import io
import json
import random

from flask import Blueprint, jsonify, send_file, request
from flask_login import login_required

from app.extensions import db
from app.models import (
    User,
    Order,
    Transaction,
    Dispute,
    Withdrawal,
)

# =====================================================
# BLUEPRINT
# =====================================================

analytics = Blueprint(
    "analytics",
    __name__,
    url_prefix="/api/analytics",
)

# =====================================================
# SIMPLE ML FRAUD SCORER (HEURISTIC BASED)
# =====================================================

def ml_fraud_score(order):

    score = 0.0

    if order.total_price > 300_000:
        score += 0.25

    if order.buyer.strike_count > 1:
        score += 0.2

    if order.listing.seller.merchant_tier == "Novice":
        score += 0.15

    recent_tx = Transaction.query.filter(
        Transaction.user_id == order.buyer_id,
        Transaction.timestamp >= datetime.utcnow() - timedelta(hours=12)
    ).count()

    if recent_tx > 6:
        score += 0.25

    disputes = Dispute.query.filter_by(claimant_id=order.buyer_id).count()
    if disputes > 2:
        score += 0.2

    return min(score, 1.0)


# =====================================================
# KPI GENERATORS
# =====================================================

def kpis():

    users = User.query.count()
    orders = Order.query.count()

    revenue = (
        db.session.query(db.func.sum(Transaction.amount))
        .filter(Transaction.type == "PlatformFee")
        .scalar()
        or 0
    )

    disputes = Dispute.query.count()

    return {
        "users": users,
        "orders": orders,
        "revenue": revenue,
        "open_disputes": disputes,
    }


# =====================================================
# TAX & REGULATORY EXPORT
# =====================================================

@analytics.route("/exports/tax")
@login_required
def export_tax():

    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow([
        "user_id",
        "tx_id",
        "amount",
        "timestamp",
        "reference",
    ])

    txs = Transaction.query.all()

    for tx in txs:
        writer.writerow([
            tx.user_id,
            tx.id,
            tx.amount,
            tx.timestamp,
            tx.reference,
        ])

    buf.seek(0)

    return send_file(
        io.BytesIO(buf.getvalue().encode()),
        mimetype="text/csv",
        download_name="fliptrybe_tax_export.csv",
        as_attachment=True,
    )


# =====================================================
# FRAUD AUDIT EXPORT
# =====================================================

@analytics.route("/exports/fraud")
@login_required
def export_fraud():

    data = []

    orders = Order.query.all()

    for o in orders:
        data.append({
            "order_id": o.id,
            "buyer": o.buyer_id,
            "seller": o.listing.user_id,
            "fraud_score": ml_fraud_score(o),
        })

    return jsonify(data)


# =====================================================
# PLATFORM HEALTH CHECK
# =====================================================

@analytics.route("/health")
@login_required
def platform_health():

    return jsonify(kpis())


print("📊 Segment 13 Loaded: Analytics Grid Activated")