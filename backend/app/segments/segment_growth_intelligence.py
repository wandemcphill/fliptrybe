"""
=====================================================
FLIPTRYBE SEGMENT 6
GROWTH INTELLIGENCE ENGINE
MERCHANT LEADERBOARDS • WATCHLISTS
SIGNALS • DASHBOARDS • REGIONAL RANKING
=====================================================
Do not merge yet.
"""

from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from sqlalchemy import func, desc

from app.extensions import db
from app.models import User, Listing, Order, Transaction

from app.segments.segment_notifications_engine import dispatch_notification

# =====================================================
# MODELS
# =====================================================

class Watchlist(db.Model):

    __tablename__ = "watchlists"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, nullable=False)
    listing_id = db.Column(db.Integer, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MerchantFollow(db.Model):

    __tablename__ = "merchant_follows"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer)
    merchant_id = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ListingMetric(db.Model):

    __tablename__ = "listing_metrics"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)

    listing_id = db.Column(db.Integer)

    views = db.Column(db.Integer, default=0)
    saves = db.Column(db.Integer, default=0)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


class MerchantWeeklyStat(db.Model):

    __tablename__ = "merchant_weekly_stats"

    id = db.Column(db.Integer, primary_key=True)

    merchant_id = db.Column(db.Integer)
    week = db.Column(db.String(20))

    total_sales = db.Column(db.Float, default=0.0)
    orders_count = db.Column(db.Integer, default=0)


# =====================================================
# BLUEPRINT
# =====================================================

growth = Blueprint(
    "growth",
    __name__,
    url_prefix="/api/growth",
)

# =====================================================
# WATCHLIST
# =====================================================

@growth.route("/watch/<int:listing_id>", methods=["POST"])
@login_required
def watch_listing(listing_id):

    existing = Watchlist.query.filter_by(
        user_id=current_user.id,
        listing_id=listing_id,
    ).first()

    if existing:
        return jsonify({"status": "already"})

    db.session.add(
        Watchlist(
            user_id=current_user.id,
            listing_id=listing_id,
        )
    )
    db.session.commit()

    return jsonify({"status": "watching"})


# =====================================================
# FOLLOW MERCHANT
# =====================================================

@growth.route("/follow/<int:merchant_id>", methods=["POST"])
@login_required
def follow_merchant(merchant_id):

    if merchant_id == current_user.id:
        return jsonify({"error": "Cannot follow yourself"}), 400

    existing = MerchantFollow.query.filter_by(
        user_id=current_user.id,
        merchant_id=merchant_id,
    ).first()

    if existing:
        return jsonify({"status": "already"})

    db.session.add(
        MerchantFollow(
            user_id=current_user.id,
            merchant_id=merchant_id,
        )
    )
    db.session.commit()

    return jsonify({"status": "following"})


# =====================================================
# LISTING SIGNALS
# =====================================================

@growth.route("/signal/<int:listing_id>", methods=["POST"])
@login_required
def signal_listing(listing_id):

    data = request.json or {}
    signal = data.get("type", "view")

    metric = ListingMetric.query.filter_by(listing_id=listing_id).first()

    if not metric:
        metric = ListingMetric(listing_id=listing_id)
        db.session.add(metric)

    if signal == "view":
        metric.views += 1

    if signal == "save":
        metric.saves += 1

    metric.updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({"status": "recorded"})


# =====================================================
# MERCHANT LEADERBOARD
# =====================================================

@growth.route("/leaderboard/national")
def national():

    rows = (
        db.session.query(
            User.id,
            User.name,
            func.sum(Transaction.amount).label("total"),
        )
        .join(Transaction, Transaction.user_id == User.id)
        .filter(User.is_admin == False)
        .group_by(User.id)
        .order_by(desc("total"))
        .limit(50)
        .all()
    )

    return jsonify(
        [
            {"merchant_id": r.id, "name": r.name, "total_sales": r.total}
            for r in rows
        ]
    )


@growth.route("/leaderboard/state/<state>")
def by_state(state):

    rows = (
        db.session.query(
            User.id,
            User.name,
            func.sum(Transaction.amount).label("total"),
        )
        .join(Transaction)
        .filter(User.state == state)
        .group_by(User.id)
        .order_by(desc("total"))
        .limit(20)
        .all()
    )

    return jsonify(
        [
            {"merchant_id": r.id, "name": r.name, "total_sales": r.total}
            for r in rows
        ]
    )


# =====================================================
# MERCHANT DASHBOARD
# =====================================================

@growth.route("/merchant/dashboard")
@login_required
def merchant_dashboard():

    sales = (
        db.session.query(func.sum(Transaction.amount))
        .filter(Transaction.user_id == current_user.id)
        .scalar()
        or 0
    )

    orders = (
        Order.query.filter_by(buyer_id=current_user.id).count()
    )

    followers = MerchantFollow.query.filter_by(
        merchant_id=current_user.id
    ).count()

    listings = Listing.query.filter_by(
        user_id=current_user.id
    ).count()

    return jsonify(
        {
            "wallet": current_user.wallet_balance,
            "total_sales": sales,
            "orders": orders,
            "followers": followers,
            "listings": listings,
        }
    )


# =====================================================
# WEEKLY RANK REFRESH
# =====================================================

def refresh_weekly_rankings():

    start = datetime.utcnow() - timedelta(days=7)

    rows = (
        db.session.query(
            User.id,
            func.sum(Transaction.amount).label("total"),
            func.count(Order.id).label("orders"),
        )
        .join(Transaction)
        .join(Order, Order.listing_id == Transaction.id, isouter=True)
        .group_by(User.id)
        .all()
    )

    week = datetime.utcnow().strftime("%Y-W%U")

    for r in rows:
        stat = MerchantWeeklyStat.query.filter_by(
            merchant_id=r.id,
            week=week,
        ).first()

        if not stat:
            stat = MerchantWeeklyStat(
                merchant_id=r.id,
                week=week,
            )

        stat.total_sales = r.total or 0
        stat.orders_count = r.orders or 0

        db.session.add(stat)

    db.session.commit()


# =====================================================
# MERCHANT LISTING ALERTS
# =====================================================

def notify_followers_new_listing(listing):

    followers = MerchantFollow.query.filter_by(
        merchant_id=listing.user_id
    ).all()

    for f in followers:
        dispatch_notification(
            f.user_id,
            "New Listing 🚀",
            f"{listing.title} just dropped!",
            ("sms", "whatsapp"),
        )


print("🏆 Segment 6 Loaded: Growth Intelligence Online")