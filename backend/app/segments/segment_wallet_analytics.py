from __future__ import annotations

from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import User, WalletTxn
from app.utils.jwt_utils import decode_token

analytics_bp = Blueprint("analytics_bp", __name__, url_prefix="/api/wallet/analytics")

_INIT = False


@analytics_bp.before_app_request
def _ensure_tables_once():
    global _INIT
    if _INIT:
        return
    try:
        db.create_all()
    except Exception:
        pass
    _INIT = True


def _bearer():
    h = request.headers.get("Authorization", "")
    if not h.startswith("Bearer "):
        return None
    return h.replace("Bearer ", "", 1).strip()


def _current_user():
    tok = _bearer()
    if not tok:
        return None
    payload = decode_token(tok)
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


@analytics_bp.get("")
def my_analytics():
    u = _current_user()
    if not u:
        return jsonify({"message": "Unauthorized"}), 401
    days = int(request.args.get("days") or 14)
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.session.query(db.func.date(WalletTxn.created_at).label("d"), db.func.sum(WalletTxn.amount).label("amt"))
        .filter(WalletTxn.user_id == int(u.id), WalletTxn.direction == "credit", WalletTxn.created_at >= since)
        .group_by("d")
        .order_by("d")
        .all()
    )
    out = [{"date": str(d), "amount": float(amt or 0.0)} for d, amt in rows]
    return jsonify({"ok": True, "user_id": int(u.id), "role": u.role or "buyer", "days": days, "series": out}), 200
