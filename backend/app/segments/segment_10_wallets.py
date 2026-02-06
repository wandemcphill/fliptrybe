"""
=====================================================
FLIPTRYBE SEGMENT 10
IDENTITY ENGINE
KYC • MERCHANT • DRIVER
VIDEO LIVENESS • WITHDRAWAL GATES
=====================================================
Do not merge yet.
"""

import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User

from app.segments.segment_notifications_engine import dispatch_notification

# =====================================================
# MODELS
# =====================================================

class KYCRecord(db.Model):

    __tablename__ = "kyc_records"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, unique=True)

    id_type = db.Column(db.String(50))
    id_number = db.Column(db.String(80))

    face_image = db.Column(db.String(200))
    face_video = db.Column(db.String(200))

    document_image = db.Column(db.String(200))

    status = db.Column(db.String(20), default="Pending")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DriverProfile(db.Model):

    __tablename__ = "driver_profiles"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, unique=True)

    vehicle_type = db.Column(db.String(30))
    plate_number = db.Column(db.String(30))

    vehicle_photo = db.Column(db.String(200))

    status = db.Column(db.String(20), default="Pending")


class MerchantProfile(db.Model):

    __tablename__ = "merchant_profiles"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, unique=True)

    business_name = db.Column(db.String(150))
    tier = db.Column(db.String(30))

    status = db.Column(db.String(20), default="Pending")


# =====================================================
# BLUEPRINT
# =====================================================

identity = Blueprint(
    "identity",
    __name__,
    url_prefix="/api/identity",
)

# =====================================================
# SUBMIT KYC
# =====================================================

@identity.route("/submit", methods=["POST"])
@login_required
def submit_kyc():

    data = request.json

    rec = KYCRecord(
        user_id=current_user.id,
        id_type=data["id_type"],
        id_number=data["id_number"],
        face_image=data["face_image"],
        face_video=data["face_video"],
        document_image=data["document_image"],
    )

    db.session.add(rec)
    db.session.commit()

    dispatch_notification(
        current_user,
        "KYC Submitted 📄",
        "Your verification is being reviewed.",
        ("sms",),
    )

    return jsonify({"status": "submitted"})


# =====================================================
# DRIVER APPLY
# =====================================================

@identity.route("/driver/apply", methods=["POST"])
@login_required
def driver_apply():

    data = request.json

    prof = DriverProfile(
        user_id=current_user.id,
        vehicle_type=data["vehicle_type"],
        plate_number=data["plate_number"],
        vehicle_photo=data["vehicle_photo"],
    )

    db.session.add(prof)
    db.session.commit()

    dispatch_notification(
        current_user,
        "Driver Application 🚚",
        "Documents received. Screening in progress.",
        ("sms",),
    )

    return jsonify({"status": "submitted"})


# =====================================================
# MERCHANT APPLY
# =====================================================

@identity.route("/merchant/apply", methods=["POST"])
@login_required
def merchant_apply():

    data = request.json

    prof = MerchantProfile(
        user_id=current_user.id,
        business_name=data["business_name"],
        tier="Starter",
    )

    db.session.add(prof)
    db.session.commit()

    dispatch_notification(
        current_user,
        "Merchant Application 🏪",
        "We are reviewing your business profile.",
        ("sms",),
    )

    return jsonify({"status": "submitted"})


# =====================================================
# ADMIN REVIEW
# =====================================================

@identity.route("/admin/review/<int:user_id>", methods=["POST"])
@login_required
def admin_review(user_id):

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    data = request.json

    rec = KYCRecord.query.filter_by(user_id=user_id).first()
    prof = MerchantProfile.query.filter_by(user_id=user_id).first()
    driver = DriverProfile.query.filter_by(user_id=user_id).first()

    status = data["status"]

    if rec:
        rec.status = status

    if prof:
        prof.status = status

    if driver:
        driver.status = status

    if status == "Approved":
        user = User.query.get(user_id)
        user.is_verified = True

    db.session.commit()

    dispatch_notification(
        user,
        "Verification Update 🔍",
        f"Your status is now {status}",
        ("sms", "whatsapp"),
    )

    return jsonify({"status": status})


# =====================================================
# WITHDRAWAL GATE
# =====================================================

def require_verified_for_withdrawal(user):

    rec = KYCRecord.query.filter_by(user_id=user.id).first()

    return rec and rec.status == "Approved"


print("🛂 Segment 10 Loaded: Identity Engine Online")