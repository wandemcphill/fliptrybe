from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import User, AuditLog
from app.utils.jwt_utils import decode_token

driver_avail_bp = Blueprint("driver_avail_bp", __name__, url_prefix="/api/driver")

_INIT = False


@driver_avail_bp.before_app_request
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


@driver_avail_bp.post("/availability")
def set_availability():
    u = _current_user()
    if not u:
        return jsonify({"message": "Unauthorized"}), 401
    if (u.role or "") != "driver":
        return jsonify({"message": "Driver role required"}), 403

    data = request.get_json(silent=True) or {}
    is_available = bool(data.get("is_available", True))
    u.is_available = is_available
    db.session.add(u)
    try:
        db.session.add(AuditLog(actor_user_id=int(u.id), action="driver_availability", target_type="user", target_id=int(u.id), meta=f"is_available={is_available}"))
        db.session.commit()
    except Exception:
        db.session.rollback()
        try:
            db.session.add(u)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({"message": "Failed"}), 500

    return jsonify({"ok": True, "user": u.to_dict()}), 200
