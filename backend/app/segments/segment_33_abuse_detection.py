"""
=====================================================
FLIPTRYBE SEGMENT 33
ADMIN FINANCIAL CONTROL & GOVERNANCE
=====================================================
Do not merge yet.
"""

from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, Withdrawal, Transaction


# =====================================================
# BLUEPRINT
# =====================================================

admin_finance = Blueprint(
    "admin_finance",
    __name__,
    url_prefix="/admin/finance",
)


# =====================================================
# MODELS
# =====================================================

class AdminSetting(db.Model):
    __tablename__ = "admin_settings"

    id = db.Column(db.Integer, primary_key=True)

    auto_payouts = db.Column(db.Boolean, default=True)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


class ReconciliationLog(db.Model):
    __tablename__ = "reconciliation_logs"

    id = db.Column(db.Integer, primary_key=True)

    reference = db.Column(db.String(100))
    amount = db.Column(db.Float)

    gateway = db.Column(db.String(30))
    status = db.Column(db.String(30))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================
# HELPERS
# =====================================================

def auto_payout_enabled():

    cfg = AdminSetting.query.first()

    if not cfg:
        cfg = AdminSetting(auto_payouts=True)
        db.session.add(cfg)
        db.session.commit()

    return cfg.auto_payouts


# =====================================================
# ROUTES
# =====================================================

@admin_finance.route("/toggle-auto-payout", methods=["POST"])
@login_required
def toggle_auto():

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    cfg = AdminSetting.query.first()

    cfg.auto_payouts = not cfg.auto_payouts

    db.session.commit()

    return jsonify({"auto_payouts": cfg.auto_payouts})


@admin_finance.route("/ban-user/<int:user_id>", methods=["POST"])
@login_required
def ban(user_id):

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    u = User.query.get_or_404(user_id)
    u.is_frozen = True

    db.session.commit()

    return jsonify({"status": "banned"})


@admin_finance.route("/reconciliation", methods=["POST"])
@login_required
def reconcile():

    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    data = request.json

    row = ReconciliationLog(**data)

    db.session.add(row)
    db.session.commit()

    return jsonify({"status": "logged"})


print("🏦 Segment 33 Loaded: Admin Finance Control Online")