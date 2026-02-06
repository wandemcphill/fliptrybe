"""
=====================================================
FLIPTRYBE SEGMENT 17
MERCHANT INTELLIGENCE LAYER
=====================================================
Do not merge yet.
"""

from datetime import datetime, timedelta

from flask import Blueprint, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, Order, Listing

# =====================================================
# BLUEPRINT
# =====================================================

merchant_intel = Blueprint(
    "merchant_intel",
    __name__,
    url_prefix="/api/merchant-intel",
)

# =====================================================
# MODELS
# =====================================================

class MerchantStats(db.Model):
    __tablename__ = "merchant_stats"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, index=True)
    total_sales = db.Column(db.Float, default=0)
    weekly_sales = db.Column(db.Float, default=0)
    deliveries_completed = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)


class MerchantTierHistory(db.Model):
    __tablename__ = "merchant_tiers"

    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer)
    tier = db.Column(db.String(20))
    effective_date = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================
# TIER ENGINE
# =====================================================

TIERS = [
    ("Novice", 0),
    ("Bronze", 1_000_000),
    ("Silver", 5_000_000),
    ("Gold", 15_000_000),
    ("Platinum", 40_000_000),
]


def evaluate_merchant_tier(merchant):

    stats = MerchantStats.query.filter_by(
        merchant_id=merchant.id
    ).first()

    if not stats:
        return "Novice"

    for tier, threshold in reversed(TIERS):
        if stats.total_sales >= threshold:
            return tier

    return "Novice"


def apply_tier_upgrade(merchant):

    new_tier = evaluate_merchant_tier(merchant)

    if merchant.merchant_tier != new_tier:

        merchant.merchant_tier = new_tier

        history = MerchantTierHistory(
            merchant_id=merchant.id,
            tier=new_tier,
        )

        db.session.add(history)
        db.session.commit()


# =====================================================
# STATS AGGREGATION
# =====================================================

def refresh_merchant_stats(merchant_id):

    completed = Order.query.filter_by(
        status="Completed"
    ).join(Listing).filter(
        Listing.user_id == merchant_id
    )

    total = sum(o.total_price for o in completed)

    weekly_cutoff = datetime.utcnow() - timedelta(days=7)

    weekly = sum(
        o.total_price
        for o in completed
        if o.timestamp >= weekly_cutoff
    )

    deliveries = completed.count()

    stats = MerchantStats.query.filter_by(
        merchant_id=merchant_id
    ).first()

    if not stats:
        stats = MerchantStats(merchant_id=merchant_id)

    stats.total_sales = total
    stats.weekly_sales = weekly
    stats.deliveries_completed = deliveries
    stats.last_updated = datetime.utcnow()

    db.session.add(stats)
    db.session.commit()

    merchant = User.query.get(merchant_id)
    apply_tier_upgrade(merchant)


# =====================================================
# DASHBOARD
# =====================================================

@merchant_intel.route("/dashboard")
@login_required
def merchant_dashboard():

    if not current_user.merchant_tier:
        return jsonify({"error": "Not a merchant"}), 403

    refresh_merchant_stats(current_user.id)

    stats = MerchantStats.query.filter_by(
        merchant_id=current_user.id
    ).first()

    return jsonify({
        "tier": current_user.merchant_tier,
        "total_sales": stats.total_sales,
        "weekly_sales": stats.weekly_sales,
        "deliveries": stats.deliveries_completed,
    })


# =====================================================
# LEADERBOARDS
# =====================================================

@merchant_intel.route("/leaderboard/national")
def national_board():

    rows = MerchantStats.query.order_by(
        MerchantStats.total_sales.desc()
    ).limit(10)

    return jsonify([
        {
            "merchant_id": r.merchant_id,
            "total": r.total_sales,
        }
        for r in rows
    ])


@merchant_intel.route("/leaderboard/weekly")
def weekly_board():

    rows = MerchantStats.query.order_by(
        MerchantStats.weekly_sales.desc()
    ).limit(10)

    return jsonify([
        {
            "merchant_id": r.merchant_id,
            "weekly": r.weekly_sales,
        }
        for r in rows
    ])


# =====================================================
# REGION BOARD STUB
# =====================================================

@merchant_intel.route("/leaderboard/state/<state>")
def state_board(state):

    rows = (
        MerchantStats.query
        .join(User, User.id == MerchantStats.merchant_id)
        .filter(User.phone != None)  # placeholder geo
        .order_by(MerchantStats.total_sales.desc())
        .limit(10)
    )

    return jsonify([
        {
            "merchant_id": r.merchant_id,
            "total": r.total_sales,
        }
        for r in rows
    ])


print("🏆 Segment 17 Loaded: Merchant Intelligence Online")