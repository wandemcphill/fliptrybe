"""
=====================================================
FLIPTRYBE SEGMENT 21
AI DISCOVERY & PERSONALIZATION LAYER
=====================================================
Do not merge yet.
"""

from datetime import datetime
from collections import defaultdict

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from sqlalchemy import or_, func

from app.extensions import db
from app.models import Listing, User
from app.realtime.socket import broadcast_feed_event


# =====================================================
# BLUEPRINT
# =====================================================

discovery = Blueprint('discovery_segment_21_realtime',
    __name__,
    url_prefix="/api/discovery",
)


# =====================================================
# MODELS
# =====================================================

class ListingSignal(db.Model):
    __tablename__ = "listing_signals"

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    signal_type = db.Column(db.String(20))  # view/save/follow
    weight = db.Column(db.Integer, default=1)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class WatchList(db.Model):
    __tablename__ = "watchlists"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    listing_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================
# SIGNAL INGESTION
# =====================================================

def ingest_listing_signal(user_id, listing_id, signal_type):

    weights = {
        "view": 1,
        "click": 2,
        "watch": 4,
        "purchase": 10,
    }

    sig = ListingSignal(
        user_id=user_id,
        listing_id=listing_id,
        signal_type=signal_type,
        weight=weights.get(signal_type, 1),
    )

    db.session.add(sig)
    db.session.commit()

    broadcast_feed_event({
        "type": "listing_signal",
        "listing_id": listing_id,
    })


# =====================================================
# RANKING ENGINE
# =====================================================

def rank_listings(query=None, state=None):

    base = Listing.query.filter(
        Listing.status == "Available"
    )

    if state:
        base = base.filter(Listing.state == state)

    scored = []

    for listing in base:

        score = 0

        signals = ListingSignal.query.filter_by(
            listing_id=listing.id
        )

        score += sum(s.weight for s in signals)

        if query and query.lower() in listing.title.lower():
            score += 15

        scored.append((listing, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    return [l for l, _ in scored]


# =====================================================
# ROUTES
# =====================================================

@discovery.route("/search")
def ai_search():

    query = request.args.get("q")
    state = request.args.get("state")

    ranked = rank_listings(query, state)

    return jsonify([
        {
            "id": l.id,
            "title": l.title,
            "price": l.price,
        }
        for l in ranked[:50]
    ])


@discovery.route("/watch/<int:listing_id>", methods=["POST"])
@login_required
def add_watch():

    row = WatchList.query.filter_by(
        user_id=current_user.id,
        listing_id=listing_id,
    ).first()

    if not row:
        db.session.add(
            WatchList(
                user_id=current_user.id,
                listing_id=listing_id,
            )
        )

        ingest_listing_signal(
            current_user.id,
            listing_id,
            "watch",
        )

    return jsonify({"status": "watching"})


@discovery.route("/click/<int:listing_id>", methods=["POST"])
def click_track(listing_id):

    ingest_listing_signal(
        None,
        listing_id,
        "click",
    )

    return jsonify({"status": "tracked"})


print("🧠 Segment 21 Loaded: AI Discovery Engine Online")