"""
=====================================================
FLIPTRYBE SEGMENT 23
ADMIN OPERATIONS CONTROL PLANE
=====================================================
Do not merge yet.
"""

from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import (
    User,
    Order,
    Transaction,
    Withdrawal,
    Dispute,
)


# =====================================================
# BLUEPRINT
# =====================================================

admin_ops = Blueprint(
    "admin_ops",
    __name__,
    url_prefix="/admin/ops",
)


# =====================================================
# MODELS
# =====================================================

class AdminActionLog(db.Model):
    __tablename__ = "admin_action_logs"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer)
    target_user_id = db.Column(db.Integer)
    action = db.Column(db.String(80))
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PaymentReconciliation(db.Model):
    __tablename__ = "payment_reconciliations"

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(80))
    amount = db.Column(db.Float)
    matched = db.Column(db.Boolean, default=False)
    reviewed_by = db.Column(db.Integer)
    reviewed_at = db.Column(db.DateTime)


# =====================================================
# HELPERS
# =====================================================

def log_admin_action(admin_id, target_user_id, action, reason=""):

    rec = AdminActionLog(
        admin_id=admin_id,
        target_user_id=target_user_id,
        action=action,
        reason=reason,
    )

    db.session.add(rec)
    db.session.commit()


# =====================================================
# USER CONTROLS
# =====================================================

@admin_ops.route("/ban/<int:user_id>", methods=["POST"])
@login_required
def ban_user(user_id):

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    user = User.query.get_or_404(user_id)
    user.is_frozen = True

    db.session.commit()

    log_admin_action(
        current_user.id,
        user_id,
        "ban",
        request.json.get("reason", ""),
    )

    return jsonify({"status": "banned"})


@admin_ops.route("/unban/<int:user_id>", methods=["POST"])
@login_required
def unban_user(user_id):

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    user = User.query.get_or_404(user_id)
    user.is_frozen = False

    db.session.commit()

    log_admin_action(
        current_user.id,
        user_id,
        "unban",
    )

    return jsonify({"status": "unbanned"})


@admin_ops.route("/make-merchant/<int:user_id>", methods=["POST"])
@login_required
def promote_merchant(user_id):

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    user = User.query.get_or_404(user_id)
    user.merchant_tier = "Novice"

    db.session.commit()

    log_admin_action(
        current_user.id,
        user_id,
        "merchant_onboard",
    )

    return jsonify({"status": "merchant_created"})


# =====================================================
# DISPUTE MANAGEMENT
# =====================================================

@admin_ops.route("/disputes")
@login_required
def list_disputes():

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    rows = Dispute.query.order_by(
        Dispute.created_at.desc()
    )

    return jsonify([
        {
            "id": d.id,
            "order": d.order_id,
            "status": d.status,
            "reason": d.reason,
        }
        for d in rows
    ])


@admin_ops.route("/disputes/<int:dispute_id>/resolve", methods=["POST"])
@login_required
def resolve_dispute(dispute_id):

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    dispute = Dispute.query.get_or_404(dispute_id)

    dispute.status = "Resolved"

    db.session.commit()

    log_admin_action(
        current_user.id,
        dispute.claimant_id,
        "dispute_resolved",
    )

    return jsonify({"status": "resolved"})


# =====================================================
# PAYMENT RECONCILIATION
# =====================================================

@admin_ops.route("/reconcile", methods=["POST"])
@login_required
def reconcile_payment():

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    data = request.json

    rec = PaymentReconciliation(
        reference=data["reference"],
        amount=data["amount"],
        matched=data["matched"],
        reviewed_by=current_user.id,
        reviewed_at=datetime.utcnow(),
    )

    db.session.add(rec)
    db.session.commit()

    log_admin_action(
        current_user.id,
        None,
        "payment_reconciled",
    )

    return jsonify({"status": "recorded"})


print("⚙️ Segment 23 Loaded: Admin Ops Online")