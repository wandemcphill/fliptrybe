"""
==================================================
FLIPTRYBE SEGMENT 2
FEED INTELLIGENCE ENGINE
Signals • Ranking • Trending • Geo Boost
==================================================
Built AFTER Genesis.
Do not merge yet.
"""

from datetime import datetime, timedelta
import math

from flask import Blueprint, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, Listing

# ==================================================
# DATABASE TABLES
# ==================================================

class FeedSignal(db.Model):
    __tablename__ = "feed_signals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    listing_id = db.Column(db.Integer)
    signal_type = db.Column(db.String(20))
    weight = db.Column(db.Float, default=1.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FeedScore(db.Model):
    __tablename__ = "feed_scores"

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, unique=True)
    score = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)


# ==================================================
# SIGNAL INGESTION
# ==================================================

SIGNAL_WEIGHTS = {
    "view": 1,
    "save": 3,
    "share": 4,
    "message": 5,
    "purchase": 10,
}


def ingest_feed_signal(user_id, listing_id, signal_type):

    weight = SIGNAL_WEIGHTS.get(signal_type, 1)

    s = FeedSignal(
        user_id=user_id,
        listing_id=listing_id,
        signal_type=signal_type,
        weight=weight,
    )

    db.session.add(s)
    db.session.commit()

    recompute_listing_score(listing_id)


# ==================================================
# RANKING ENGINE
# ==================================================

DECAY_HALF_LIFE = 6  # hours


def time_decay(hours):
    return math.exp(-hours / DECAY_HALF_LIFE)


def recompute_listing_score(listing_id):

    since = datetime.utcnow() - timedelta(days=3)

    signals = FeedSignal.query.filter(
        FeedSignal.listing_id == listing_id,
        FeedSignal.created_at >= since,
    ).all()

    score = 0.0

    now = datetime.utcnow()

    for s in signals:
        age_hours = (now - s.created_at).total_seconds() / 3600
        score += s.weight * time_decay(age_hours)

    fs = FeedScore.query.filter_by(listing_id=listing_id).first()

    if not fs:
        fs = FeedScore(listing_id=listing_id, score=score)
        db.session.add(fs)
    else:
        fs.score = score
        fs.last_updated = now

    db.session.commit()


# ==================================================
# TRENDING ENGINE
# ==================================================

def trending_listings(limit=20):

    cutoff = datetime.utcnow() - timedelta(hours=12)

    return (
        db.session.query(Listing)
        .join(FeedScore, FeedScore.listing_id == Listing.id)
        .filter(FeedScore.last_updated >= cutoff)
        .order_by(FeedScore.score.desc())
        .limit(limit)
        .all()
    )


# ==================================================
# PERSONALIZATION
# ==================================================

def user_interest_profile(user_id):

    rows = (
        db.session.query(Listing.category, db.func.sum(FeedSignal.weight))
        .join(FeedSignal, FeedSignal.listing_id == Listing.id)
        .filter(FeedSignal.user_id == user_id)
        .group_by(Listing.category)
        .all()
    )

    return {cat: w for cat, w in rows}


# ==================================================
# GEO BOOSTING
# ==================================================

GEO_WEIGHT = 1.25


def geo_boost(user: User, listing: Listing):

    if not listing.state:
        return 1.0

    if listing.state.lower() in (user.phone or "").lower():
        return GEO_WEIGHT

    return 1.0


# ==================================================
# FEED GENERATOR
# ==================================================

def build_feed_for_user(user: User, limit=40):

    interests = user_interest_profile(user.id)

    base = (
        db.session.query(Listing, FeedScore.score)
        .join(FeedScore, FeedScore.listing_id == Listing.id)
        .filter(Listing.status == "Available")
        .all()
    )

    ranked = []

    for listing, score in base:

        cat_boost = 1.0 + (interests.get(listing.category, 0) / 50)
        geo = geo_boost(user, listing)

        final = score * cat_boost * geo

        ranked.append((final, listing))

    ranked.sort(reverse=True, key=lambda x: x[0])

    return [l for _, l in ranked[:limit]]


# ==================================================
# FEED ROUTES
# ==================================================

feed_engine = Blueprint(
    "feed_engine",
    __name__,
    url_prefix="/api/feed-engine"
)


@feed_engine.route("/my-feed")
@login_required
def my_feed():

    feed = build_feed_for_user(current_user)

    return jsonify([
        {
            "id": l.id,
            "title": l.title,
            "price": l.price,
            "state": l.state,
        }
        for l in feed
    ])


@feed_engine.route("/signal/<int:listing_id>/<signal_type>")
@login_required
def push_signal(listing_id, signal_type):

    ingest_feed_signal(current_user.id, listing_id, signal_type)

    return jsonify({"status": "ok"})


print("📡 Segment 2 Loaded: Feed Intelligence Engine")