"""
=====================================================
FLIPTRYBE SEGMENT 16
AI MARKETPLACE DISCOVERY ENGINE
=====================================================
Do not merge yet.
"""

from math import radians, cos, sin, asin, sqrt
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Listing, User

# =====================================================
# BLUEPRINT
# =====================================================

discovery = Blueprint('discovery_segment_16_fraud',
    __name__,
    url_prefix="/api/discovery",
)

# =====================================================
# MODELS (LIGHT EXTENSIONS)
# =====================================================

class Watchlist(db.Model):
    __tablename__ = "watchlists"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, index=True)
    listing_id = db.Column(db.Integer, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ListingMetric(db.Model):
    __tablename__ = "listing_metrics"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, index=True)
    views = db.Column(db.Integer, default=0)
    watchers = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    last_seen = db.Column(db.DateTime)


# =====================================================
# GEO UTILS
# =====================================================

def haversine(lat1, lon1, lat2, lon2):

    lon1, lat1, lon2, lat2 = map(radians, [
        lon1, lat1, lon2, lat2
    ])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    return 6371 * c


# =====================================================
# SEARCH
# =====================================================

@discovery.route("/search")
@login_required
def smart_search():

    query = request.args.get("q", "")
    lat = float(request.args.get("lat", 0))
    lng = float(request.args.get("lng", 0))

    qs = Listing.query.filter(
        Listing.status == "Available"
    )

    if query:
        qs = qs.filter(Listing.title.ilike(f"%{query}%"))

    results = []

    for item in qs.limit(200):

        distance = None

        if lat and lng and item.state:
            # Stub geo weight
            distance = 50

        score = 1

        metric = ListingMetric.query.filter_by(
            listing_id=item.id
        ).first()

        if metric:
            score += metric.views * 0.01
            score += metric.watchers * 0.03

        results.append({
            "id": item.id,
            "title": item.title,
            "price": item.price,
            "distance": distance,
            "score": round(score, 2),
        })

    results.sort(
        key=lambda x: (-x["score"], x["distance"] or 9999)
    )

    return jsonify(results[:50])


# =====================================================
# CLICK TRACKING
# =====================================================

@discovery.route("/click/<int:listing_id>", methods=["POST"])
@login_required
def click(listing_id):

    metric = ListingMetric.query.filter_by(
        listing_id=listing_id
    ).first()

    if not metric:
        metric = ListingMetric(listing_id=listing_id)

    metric.clicks += 1
    metric.views += 1
    metric.last_seen = datetime.utcnow()

    db.session.add(metric)
    db.session.commit()

    return jsonify({"ok": True})


# =====================================================
# WATCHLIST
# =====================================================

@discovery.route("/watch/<int:listing_id>", methods=["POST"])
@login_required
def watch(listing_id):

    existing = Watchlist.query.filter_by(
        user_id=current_user.id,
        listing_id=listing_id,
    ).first()

    if existing:
        return jsonify({"status": "already"})

    w = Watchlist(
        user_id=current_user.id,
        listing_id=listing_id,
    )

    db.session.add(w)

    metric = ListingMetric.query.filter_by(
        listing_id=listing_id
    ).first()

    if not metric:
        metric = ListingMetric(listing_id=listing_id)

    metric.watchers += 1

    db.session.add(metric)
    db.session.commit()

    return jsonify({"watched": True})


# =====================================================
# UNWATCH
# =====================================================

@discovery.route("/unwatch/<int:listing_id>", methods=["POST"])
@login_required
def unwatch(listing_id):

    Watchlist.query.filter_by(
        user_id=current_user.id,
        listing_id=listing_id,
    ).delete()

    metric = ListingMetric.query.filter_by(
        listing_id=listing_id
    ).first()

    if metric and metric.watchers > 0:
        metric.watchers -= 1

    db.session.commit()

    return jsonify({"unwatched": True})


print("🧠 Segment 16 Loaded: Discovery Engine Active")