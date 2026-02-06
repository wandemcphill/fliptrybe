from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import User, AuditLog
from app.utils.jwt_utils import decode_token

audit_bp = Blueprint("audit_bp", __name__, url_prefix="/api/admin/audit")

_INIT = False


@audit_bp.before_app_request
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
        if int(u.id or 0) == 1:
            return True
    except Exception:
        pass
    return (u.role or "") == "admin"


@audit_bp.get("")
def list_logs():
    u = _current_user()
    if not _is_admin(u):
        return jsonify([]), 200
    action = (request.args.get("action") or "").strip()
    q = AuditLog.query
    if action:
        q = q.filter(AuditLog.action.ilike(action))
    rows = q.order_by(AuditLog.created_at.desc()).limit(250).all()
    return jsonify([r.to_dict() for r in rows]), 200
