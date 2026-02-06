from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import User
from app.utils.jwt_utils import decode_token

drivers_list_bp = Blueprint("drivers_list_bp", __name__, url_prefix="/api/drivers")

_INIT_DONE = False


@drivers_list_bp.before_app_request
def _ensure_tables_once():
    global _INIT_DONE
    if _INIT_DONE:
        return
    try:
        db.create_all()
    except Exception:
        pass
    _INIT_DONE = True


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


def _role(u: User | None) -> str:
    if not u:
        return "guest"
    return (getattr(u, "role", None) or "buyer").strip().lower()


@drivers_list_bp.get("")
def list_drivers():
    u = _current_user()
    if not u:
        return jsonify([]), 200

    r = _role(u)
    if r not in ("merchant", "admin"):
        return jsonify([]), 200

    # minimal driver roster for assignment UI
    rows = User.query.filter_by(role="driver").order_by(User.created_at.desc()).limit(100).all()
    out = []
    for x in rows:
        out.append({
            "id": int(x.id),
            "name": getattr(x, "name", "") or "",
            "email": getattr(x, "email", "") or "",
        })
    return jsonify(out), 200
