"""
=====================================================
FLIPTRYBE SEGMENT 7
AI DISCOVERY ENGINE
SEARCH • GEO RANKING • SHORTLET INTEL
PERSONALIZATION • HEATMAPS
=====================================================
Do not merge yet.
"""

from datetime import datetime, timedelta
import math

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from sqlalchemy import func, desc

from app.extensions import db
from app.models import Listing, Order, User

from app.segments.segment_growth_intelligence import ListingMetric, Watchlist
from app.segments.segment_notifications_engine import dispatch_notification

# =====================================================
# MODELS
# =====================================================

class SearchQuery(db.Model):

    __tablename__ = "search_queries"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer)
    query = db.Column(db.String(255))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ShortletStat(db.Model):

    __tablename__ = "shortlet_stats"

    id = db.Column(db.Integer, primary_key=True)

    listing_id = db.Column(db.Integer)

    booking_count = db.Column(db.Integer, default=0)
    avg_rating = db.Column(db.Float, default=0)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================
# BLUEPRINT
# =====================================================

ai = Blueprint(
    "ai_discovery",
    __name__,
    url_prefix="/api/discovery",
)

# =====================================================
# GEO UTILS
# =====================================================

def distance_km(lat1, lon1, lat2, lon2):

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


# =====================================================
# RANKING FORMULA
# =====================================================

def score_listing(listing, metric, user=None, lat=None, lng=None):

    score = 0

    score += (metric.views * 0.2)
    score += (metric.saves * 0.6)

    if lat and lng:
        dist = distance_km(lat, lng, listing.lat, listing.lng)
        score += max(0, 50 - dist)

    if user:
        if Watchlist.query.filter_by(
            user_id=user.id,
            listing_id=listing.id,
        ).first():
            score += 20

    return round(score, 2)


# =====================================================
# SEARCH ENDPOINT
# =====================================================

@ai.route("/search")
@login_required
def search():

    q = request.args.get("q", "")
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)

    SearchQuery(
        user_id=current_user.id,
        query=q,
        lat=lat,
        lng=lng,
    )

    listings = Listing.query.filter(
        Listing.title.ilike(f"%{q}%")
    ).all()

    results = []

    for l in listings:

        metric = ListingMetric.query.filter_by(listing_id=l.id).first()

        if not metric:
            continue

        score = score_listing(l, metric, current_user, lat, lng)

        results.append(
            {
                "id": l.id,
                "title": l.title,
                "price": l.price,
                "score": score,
            }
        )

    results.sort(key=lambda r: r["score"], reverse=True)

    return jsonify(results)


# =====================================================
# SHORTLET BOOST
# =====================================================

def refresh_shortlet_stats():

    rows = (
        db.session.query(
            Listing.id,
            func.count(Order.id).label("cnt"),
        )
        .join(Order)
        .group_by(Listing.id)
        .all()
    )

    for r in rows:

        stat = ShortletStat.query.filter_by(listing_id=r.id).first()

        if not stat:
            stat = ShortletStat(listing_id=r.id)

        stat.booking_count = r.cnt
        stat.updated_at = datetime.utcnow()

        db.session.add(stat)

    db.session.commit()


print("🧠 Segment 7 Loaded: AI Discovery Active")