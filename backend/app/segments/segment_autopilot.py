from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import User
from app.utils.jwt_utils import decode_token
from app.utils.autopilot import get_settings, tick

autopilot_bp = Blueprint("autopilot_bp", __name__, url_prefix="/api/admin/autopilot")

_INIT = False


@autopilot_bp.before_app_request
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


def _is_admin(u):
    if not u:
        return False
    try:
        if int(getattr(u, "id", 0) or 0) == 1:
            return True
    except Exception:
        pass
    return (getattr(u, "role", "") or "").strip().lower() == "admin"


@autopilot_bp.get("")
def get_status():
    u = _current_user()
    if not _is_admin(u):
        return jsonify({"message": "Forbidden"}), 403
    s = get_settings()
    return jsonify({"ok": True, "settings": s.to_dict()}), 200


@autopilot_bp.post("/toggle")
def toggle():
    u = _current_user()
    if not _is_admin(u):
        return jsonify({"message": "Forbidden"}), 403
    s = get_settings()
    data = request.get_json(silent=True) or {}
    enabled = data.get("enabled")
    if enabled is None:
        enabled = not bool(s.enabled)
    s.enabled = bool(enabled)
    db.session.add(s)
    db.session.commit()
    return jsonify({"ok": True, "settings": s.to_dict()}), 200


@autopilot_bp.post("/tick")
def manual_tick():
    u = _current_user()
    if not _is_admin(u):
        return jsonify({"message": "Forbidden"}), 403
    res = tick()
    return jsonify(res), 200
