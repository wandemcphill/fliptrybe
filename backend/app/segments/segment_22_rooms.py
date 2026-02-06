"""
=====================================================
FLIPTRYBE SEGMENT 22
KYC & COMPLIANCE LAYER
=====================================================
Do not merge yet.
"""

from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, Withdrawal


# =====================================================
# BLUEPRINT
# =====================================================

kyc = Blueprint('kyc_segment_22_rooms',
    __name__,
    url_prefix="/api/kyc",
)


# =====================================================
# MODELS
# =====================================================

class KYCProfile(db.Model):
    __tablename__ = "kyc_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True)

    id_type = db.Column(db.String(30))  # nin/voter/passport
    id_number = db.Column(db.String(50))

    id_image = db.Column(db.String(200))
    selfie_image = db.Column(db.String(200))
    selfie_video = db.Column(db.String(200))

    verified = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)


class ComplianceEvent(db.Model):
    __tablename__ = "compliance_events"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    event_type = db.Column(db.String(40))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================
# CORE LOGIC
# =====================================================

def user_has_kyc(user_id):

    profile = KYCProfile.query.filter_by(
        user_id=user_id
    ).first()

    return bool(profile and profile.verified)


def log_compliance_event(user_id, event_type, notes=""):

    evt = ComplianceEvent(
        user_id=user_id,
        event_type=event_type,
        notes=notes,
    )

    db.session.add(evt)
    db.session.commit()


# =====================================================
# ROUTES
# =====================================================

@kyc.route("/submit", methods=["POST"])
@login_required
def submit_kyc():

    data = request.json

    profile = KYCProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not profile:
        profile = KYCProfile(user_id=current_user.id)

    profile.id_type = data["id_type"]
    profile.id_number = data["id_number"]
    profile.id_image = data["id_image"]
    profile.selfie_image = data["selfie_image"]
    profile.selfie_video = data["selfie_video"]

    db.session.add(profile)
    db.session.commit()

    log_compliance_event(
        current_user.id,
        "kyc_submitted",
    )

    return jsonify({"status": "submitted"})


@kyc.route("/status")
@login_required
def kyc_status():

    profile = KYCProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    return jsonify({
        "verified": bool(profile and profile.verified),
    })


@kyc.route("/admin/verify/<int:user_id>", methods=["POST"])
@login_required
def admin_verify(user_id):

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    profile = KYCProfile.query.filter_by(
        user_id=user_id
    ).first_or_404()

    profile.verified = True
    profile.verified_at = datetime.utcnow()

    db.session.commit()

    log_compliance_event(
        user_id,
        "kyc_verified",
    )

    return jsonify({"status": "verified"})


# =====================================================
# WITHDRAWAL GATE
# =====================================================

def withdrawal_allowed(user_id):

    user = User.query.get(user_id)

    if not user_has_kyc(user_id):
        return False, "KYC required"

    if user.is_frozen:
        return False, "Account frozen"

    return True, "OK"


@kyc.route("/withdrawal-check")
@login_required
def withdrawal_check():

    ok, reason = withdrawal_allowed(
        current_user.id
    )

    return jsonify({
        "allowed": ok,
        "reason": reason,
    })


print("🛡️ Segment 22 Loaded: KYC & Compliance Online")