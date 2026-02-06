from __future__ import annotations

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from app.extensions import db
from app.models import User, Order, Receipt
from app.utils.jwt_utils import decode_token

kpi_bp = Blueprint("kpi_bp", __name__, url_prefix="/api/kpis")

_INIT = False


@kpi_bp.before_app_request
def _ensure_tables_once():
    global _INIT
    if _INIT:
        return
    try:
        db.create_all()
    except Exception:
        pass
    _INIT = True


def _bearer_token() -> str | None:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    return header.replace("Bearer ", "", 1).strip() or None


def _current_user() -> User | None:
    token = _bearer_token()
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    sub = payload.get("sub")
    if not sub:
        return None
    try:
        uid = int(sub)
    except Exception:
        return None
    return User.query.get(uid)


@kpi_bp.get("/merchant")
def merchant_kpis():
    u = _current_user()
    if not u:
        return jsonify({"message": "Unauthorized"}), 401

    # Orders for this merchant
    total_orders = db.session.query(func.count(Order.id)).filter(Order.merchant_id == u.id).scalar() or 0
    completed = db.session.query(func.count(Order.id)).filter(Order.merchant_id == u.id, Order.status.in_(["delivered", "completed"])).scalar() or 0

    revenue = db.session.query(func.sum(Order.amount)).filter(Order.merchant_id == u.id, Order.status.in_(["delivered", "completed"])).scalar() or 0.0
    delivery = db.session.query(func.sum(Order.delivery_fee)).filter(Order.merchant_id == u.id, Order.status.in_(["delivered", "completed"])).scalar() or 0.0

    # Commission receipts for merchant
    fees = db.session.query(func.sum(Receipt.fee)).filter(Receipt.user_id == u.id).scalar() or 0.0

    return jsonify({
        "ok": True,
        "kpis": {
            "total_orders": int(total_orders),
            "completed_orders": int(completed),
            "gross_revenue": float(revenue),
            "delivery_total": float(delivery),
            "platform_fees": float(fees),
        }
    }), 200
