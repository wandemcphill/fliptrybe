"""
=====================================================
FLIPTRYBE SEGMENT 20
SHORT-LET ENGINE
=====================================================
Do not merge yet.
"""

from datetime import datetime, date, timedelta

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User
from app.realtime.socket import broadcast_feed_event


# =====================================================
# BLUEPRINT
# =====================================================

shortlets = Blueprint('shortlets_segment_20_invoices',
    __name__,
    url_prefix="/api/shortlets",
)


# =====================================================
# MODELS
# =====================================================

class Property(db.Model):
    __tablename__ = "properties"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer)
    title = db.Column(db.String(120))
    description = db.Column(db.Text)
    nightly_rate = db.Column(db.Float)

    city = db.Column(db.String(60))
    state = db.Column(db.String(60))

    score = db.Column(db.Float, default=5.0)
    review_count = db.Column(db.Integer, default=0)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PropertyMedia(db.Model):
    __tablename__ = "property_media"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer)
    filename = db.Column(db.String(200))
    media_type = db.Column(db.String(20))  # image / video


class PropertyAvailability(db.Model):
    __tablename__ = "property_availability"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer)
    day = db.Column(db.Date)
    is_booked = db.Column(db.Boolean, default=False)


class PropertyBooking(db.Model):
    __tablename__ = "property_bookings"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer)
    guest_id = db.Column(db.Integer)

    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

    total_cost = db.Column(db.Float)
    status = db.Column(db.String(20), default="Escrowed")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================
# AVAILABILITY ENGINE
# =====================================================

def is_available(property_id, start, end):

    days = PropertyAvailability.query.filter(
        PropertyAvailability.property_id == property_id,
        PropertyAvailability.day >= start,
        PropertyAvailability.day <= end,
        PropertyAvailability.is_booked == True,
    ).count()

    return days == 0


def block_days(property_id, start, end):

    d = start
    while d <= end:

        row = PropertyAvailability(
            property_id=property_id,
            day=d,
            is_booked=True,
        )

        db.session.add(row)
        d += timedelta(days=1)

    db.session.commit()


# =====================================================
# ROUTES
# =====================================================

@shortlets.route("/create", methods=["POST"])
@login_required
def create_property():

    data = request.json

    prop = Property(
        owner_id=current_user.id,
        title=data["title"],
        description=data["description"],
        nightly_rate=data["rate"],
        city=data["city"],
        state=data["state"],
    )

    db.session.add(prop)
    db.session.commit()

    broadcast_feed_event({
        "type": "new_property",
        "property_id": prop.id,
    })

    return jsonify({"property_id": prop.id})


@shortlets.route("/search")
def search_properties():

    q = Property.query.filter_by(is_active=True)

    state = request.args.get("state")
    city = request.args.get("city")

    if state:
        q = q.filter(Property.state == state)

    if city:
        q = q.filter(Property.city == city)

    return jsonify([
        {
            "id": p.id,
            "title": p.title,
            "rate": p.nightly_rate,
            "score": p.score,
        }
        for p in q.limit(50)
    ])


@shortlets.route("/book", methods=["POST"])
@login_required
def book_property():

    data = request.json

    start = date.fromisoformat(data["start"])
    end = date.fromisoformat(data["end"])

    if not is_available(data["property_id"], start, end):
        return jsonify({"error": "Not available"}), 400

    days = (end - start).days
    cost = days * data["rate"]

    booking = PropertyBooking(
        property_id=data["property_id"],
        guest_id=current_user.id,
        start_date=start,
        end_date=end,
        total_cost=cost,
    )

    db.session.add(booking)
    block_days(data["property_id"], start, end)

    return jsonify({
        "booking_id": booking.id,
        "total": cost,
    })


print("🏨 Segment 20 Loaded: Short-Lets Online")