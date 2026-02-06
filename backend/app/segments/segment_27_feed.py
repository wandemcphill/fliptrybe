"""
=====================================================
FLIPTRYBE SEGMENT 27
MERCHANT GROWTH & INCENTIVE ENGINE
=====================================================
Do not merge yet.
"""

from datetime import datetime, timedelta

from flask import Blueprint, jsonify
from flask_login import login_required, current_user

from sqlalchemy import func

from app.extensions import db
from app.models import User, Order, Transaction


# =====================================================
# BLUEPRINT
# =====================================================

merchant_growth = Blueprint(
    "merchant_growth",
    __name__,
    url_prefix="/api/merchant",
)


# =====================================================
# MODELS
# =====================================================

class MerchantStat(db.Model):
    __tablename__ = "merchant_stats"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer)

    total_sales = db.Column(db.Float, default=0)
    weekly_sales = db.Column(db.Float, default=0)

    deliveries_booked = db.Column(db.Integer, default=0)

    tier = db.Column(db.String(30), default="Novice")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================
# COMMISSION ENGINE
# =====================================================

def compute_sale_split(amount, is_top10=False):

    if is_top10:
        return {
            "merchant": amount * 0.12,
            "platform": amount * 0.03,
        }

    return {
        "merchant": amount * 0.10,
        "platform": amount * 0.05,
    }


def compute_delivery_split(amount):

    return {
        "merchant": amount * 0.05,
        "platform": amount * 0.15,
        "driver": amount * 0.80,
    }


# =====================================================
# STATS UPDATER
# =====================================================

def update_merchant_stats(merchant_id, order_total):

    stats = MerchantStat.query.filter_by(
        merchant_id=merchant_id
    ).first()

    if not stats:
        stats = MerchantStat(merchant_id=merchant_id)

    stats.total_sales += order_total
    stats.weekly_sales += order_total

    db.session.add(stats)
    db.session.commit()


# =====================================================
# ROUTES
# =====================================================

@merchant_growth.route("/dashboard")
@login_required
def merchant_dashboard():

    stats = MerchantStat.query.filter_by(
        merchant_id=current_user.id
    ).first()

    return jsonify({
        "total_sales": stats.total_sales if stats else 0,
        "weekly_sales": stats.weekly_sales if stats else 0,
        "tier": stats.tier if stats else "Novice",
    })


@merchant_growth.route("/leaderboard")
def leaderboard():

    top = MerchantStat.query.order_by(
        MerchantStat.weekly_sales.desc()
    ).limit(20)

    return jsonify([
        {
            "merchant_id": m.merchant_id,
            "weekly_sales": m.weekly_sales,
            "tier": m.tier,
        }
        for m in top
    ])


print("🏆 Segment 27 Loaded: Merchant Growth Engine Online")