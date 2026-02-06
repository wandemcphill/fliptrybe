"""
=====================================================
FLIPTRYBE SEGMENT 31
SHORTLET MARKETPLACE ENGINE
=====================================================
Do not merge yet.
"""

from datetime import date, datetime, timedelta

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from sqlalchemy import and_

from app.extensions import db
from app.models import User


# =====================================================
# BLUEPRINT
# =====================================================

shortlets = Blueprint('shortlets_segment_31_analytics',
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
    host_id = db.Column(db.Integer)

    title = db.Column(db.String(120))
    description = db.Column(db.Text)

    city = db.Column(db.String(50))
    state = db.Column(db.String(50))

    nightly_rate = db.Column(db.Float)

    active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer)

    guest_id = db.Column(db.Integer)

    check_in = db.Column(db.Date)
    check_out = db.Column(db.Date)

    total_price = db.Column(db.Float)

    status = db.Column(db.String(20), default="Escrowed")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================
# ROUTES
# =====================================================

@shortlets.route("/list", methods=["POST"])
@login_required
def create_property():

    data = request.json

    prop = Property(
        host_id=current_user.id,
        title=data["title"],
        description=data["description"],
        city=data["city"],
        state=data["state"],
        nightly_rate=data["nightly_rate"],
    )

    db.session.add(prop)
    db.session.commit()

    return jsonify({"id": prop.id})


@shortlets.route("/search")
def search_props():

    city = request.args.get("city")

    q = Property.query.filter_by(
        city=city,
        active=True,
    )

    return jsonify([
        {
            "id": p.id,
            "title": p.title,
            "price": p.nightly_rate,
        }
        for p in q
    ])


@shortlets.route("/book/<int:prop_id>", methods=["POST"])
@login_required
def book_property(prop_id):

    data = request.json

    check_in = date.fromisoformat(data["check_in"])
    check_out = date.fromisoformat(data["check_out"])

    nights = (check_out - check_in).days

    prop = Property.query.get_or_404(prop_id)

    total = nights * prop.nightly_rate

    booking = Booking(
        property_id=prop.id,
        guest_id=current_user.id,
        check_in=check_in,
        check_out=check_out,
        total_price=total,
    )

    db.session.add(booking)
    db.session.commit()

    return jsonify({"booking_id": booking.id})


print("🏡 Segment 31 Loaded: Shortlets Engine Online")