"""
=====================================================
FLIPTRYBE SEGMENT 11
SHORTLET / STAY MARKETPLACE ENGINE
Bookings • Calendar • Host Payout • Reviews
=====================================================
Do not merge yet.
"""

from datetime import datetime, timedelta
import uuid

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User

from app.segments.segment_payments_engine import escrow_hold
from app.segments.segment_notifications_engine import dispatch_notification

# =====================================================
# MODELS
# =====================================================

class StayListing(db.Model):

    __tablename__ = "stay_listings"

    id = db.Column(db.Integer, primary_key=True)

    host_id = db.Column(db.Integer)

    title = db.Column(db.String(200))
    description = db.Column(db.Text)

    lat = db.Column(db.Float)
    lng = db.Column(db.Float)

    nightly_price = db.Column(db.Float)

    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class StayCalendar(db.Model):

    __tablename__ = "stay_calendar"

    id = db.Column(db.Integer, primary_key=True)

    listing_id = db.Column(db.Integer)

    date = db.Column(db.Date)

    is_available = db.Column(db.Boolean, default=True)


class StayBooking(db.Model):

    __tablename__ = "stay_bookings"

    id = db.Column(db.Integer, primary_key=True)

    booking_ref = db.Column(db.String(36), unique=True)

    guest_id = db.Column(db.Integer)
    host_id = db.Column(db.Integer)
    listing_id = db.Column(db.Integer)

    check_in = db.Column(db.Date)
    check_out = db.Column(db.Date)

    total_price = db.Column(db.Float)

    status = db.Column(db.String(20), default="Escrowed")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class StayReview(db.Model):

    __tablename__ = "stay_reviews"

    id = db.Column(db.Integer, primary_key=True)

    booking_id = db.Column(db.Integer)

    guest_id = db.Column(db.Integer)

    rating = db.Column(db.Integer)

    comment = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================
# BLUEPRINT
# =====================================================

shortlets = Blueprint('shortlets_segment_11_listings',
    __name__,
    url_prefix="/api/stays",
)

# =====================================================
# CREATE LISTING
# =====================================================

@shortlets.route("/host/create", methods=["POST"])
@login_required
def create_stay():

    data = request.json

    listing = StayListing(
        host_id=current_user.id,
        title=data["title"],
        description=data["description"],
        lat=data["lat"],
        lng=data["lng"],
        nightly_price=data["nightly_price"],
    )

    db.session.add(listing)
    db.session.commit()

    return jsonify({"id": listing.id})


# =====================================================
# BOOK STAY
# =====================================================

@shortlets.route("/book", methods=["POST"])
@login_required
def book_stay():

    data = request.json

    days = (
        datetime.strptime(data["check_out"], "%Y-%m-%d")
        - datetime.strptime(data["check_in"], "%Y-%m-%d")
    ).days

    listing = StayListing.query.get_or_404(data["listing_id"])

    total = listing.nightly_price * days

    booking = StayBooking(
        booking_ref=str(uuid.uuid4()),
        guest_id=current_user.id,
        host_id=listing.host_id,
        listing_id=listing.id,
        check_in=datetime.strptime(data["check_in"], "%Y-%m-%d"),
        check_out=datetime.strptime(data["check_out"], "%Y-%m-%d"),
        total_price=total,
    )

    escrow_hold(current_user.id, total)

    db.session.add(booking)
    db.session.commit()

    dispatch_notification(
        User.query.get(listing.host_id),
        "New Booking 🏠",
        "A guest has booked your property.",
        ("push",),
    )

    return jsonify({"ref": booking.booking_ref})


# =====================================================
# COMPLETE STAY
# =====================================================

@shortlets.route("/complete/<int:booking_id>", methods=["POST"])
@login_required
def complete_stay(booking_id):

    booking = StayBooking.query.get_or_404(booking_id)

    if current_user.id != booking.guest_id:
        return jsonify({"error": "Forbidden"}), 403

    booking.status = "Completed"

    db.session.commit()

    return jsonify({"status": "completed"})


# =====================================================
# REVIEW
# =====================================================

@shortlets.route("/review", methods=["POST"])
@login_required
def review_stay():

    data = request.json

    rev = StayReview(
        booking_id=data["booking_id"],
        guest_id=current_user.id,
        rating=data["rating"],
        comment=data["comment"],
    )

    db.session.add(rev)
    db.session.commit()

    return jsonify({"status": "posted"})


print("🏠 Segment 11 Loaded: Shortlet Engine Online")