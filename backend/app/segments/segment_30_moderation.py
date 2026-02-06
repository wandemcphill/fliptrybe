"""
=====================================================
FLIPTRYBE SEGMENT 30
SEARCH, DISCOVERY & ENGAGEMENT ENGINE
=====================================================
Do not merge yet.
"""

from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from sqlalchemy import func

from app.extensions import db
from app.models import Listing, User


# =====================================================
# BLUEPRINT
# =====================================================

search = Blueprint(
    "search",
    __name__,
    url_prefix="/api/search",
)


# =====================================================
# MODELS
# =====================================================

class Watchlist(db.Model):
    __tablename__ = "watchlists"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    listing_id = db.Column(db.Integer)
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
    clicks = db.Column(db.Integer, default=0)

    last_viewed = db.Column(db.DateTime)


# =====================================================
# SEARCH SCORING
# =====================================================

def score_listing(metric):

    base = metric.views + (metric.saves * 3) + (metric.clicks * 2)

    recency_boost = 0
    if metric.last_viewed:
        delta = datetime.utcnow() - metric.last_viewed
        recency_boost = max(0, 48 - delta.hours)

    return base + recency_boost


# =====================================================
# ROUTES
# =====================================================

@search.route("/query")
def query():

    q = request.args.get("q", "")

    rows = Listing.query.filter(
        Listing.title.ilike(f"%{q}%")
    ).limit(100)

    return jsonify([
        {
            "id": l.id,
            "title": l.title,
            "price": l.price,
        }
        for l in rows
    ])


@search.route("/watch/<int:listing_id>", methods=["POST"])
@login_required
def watch(listing_id):

    db.session.add(
        Watchlist(
            user_id=current_user.id,
            listing_id=listing_id,
        )
    )

    db.session.commit()

    return jsonify({"status": "added"})


@search.route("/follow/<int:merchant_id>", methods=["POST"])
@login_required
def follow(merchant_id):

    db.session.add(
        MerchantFollow(
            user_id=current_user.id,
            merchant_id=merchant_id,
        )
    )

    db.session.commit()

    return jsonify({"status": "following"})


@search.route("/metrics/<int:listing_id>")
def metrics(listing_id):

    row = ListingMetric.query.filter_by(
        listing_id=listing_id
    ).first()

    return jsonify({
        "views": row.views if row else 0,
        "saves": row.saves if row else 0,
        "clicks": row.clicks if row else 0,
    })


print("🧠 Segment 30 Loaded: Search & Engagement Online")