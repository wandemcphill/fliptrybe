"""
=====================================================
FLIPTRYBE SEGMENT 32
KYC & IDENTITY VERIFICATION LAYER
=====================================================
Do not merge yet.
"""

from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User


# =====================================================
# BLUEPRINT
# =====================================================

kyc = Blueprint('kyc_segment_32_metrics',
    __name__,
    url_prefix="/api/kyc",
)


# =====================================================
# MODELS
# =====================================================

class KYCRecord(db.Model):
    __tablename__ = "kyc_records"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)

    id_type = db.Column(db.String(40))
    id_number = db.Column(db.String(80))

    selfie_image = db.Column(db.String(120))
    liveness_video = db.Column(db.String(120))

    status = db.Column(db.String(20), default="pending")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================
# ROUTES
# =====================================================

@kyc.route("/submit", methods=["POST"])
@login_required
def submit():

    data = request.form

    rec = KYCRecord(
        user_id=current_user.id,
        id_type=data["id_type"],
        id_number=data["id_number"],
        selfie_image=data.get("selfie"),
        liveness_video=data.get("video"),
    )

    db.session.add(rec)

    current_user.is_verified = False

    db.session.commit()

    return jsonify({"status": "submitted"})


@kyc.route("/status")
@login_required
def status():

    rec = KYCRecord.query.filter_by(
        user_id=current_user.id
    ).order_by(KYCRecord.created_at.desc()).first()

    return jsonify({
        "status": rec.status if rec else "none",
    })


print("📹 Segment 32 Loaded: KYC Engine Online")