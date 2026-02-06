from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.utils.reconciliation import reconcile_latest
from app.utils.jwt_utils import decode_token
from app.models import User

recon_bp = Blueprint("recon_bp", __name__, url_prefix="/api/admin/reconcile")


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


@recon_bp.post("")
def run_recon():
    u = _current_user()
    if not u or (u.role or "") != "admin":
        return jsonify({"message": "Admin required"}), 403
    data = request.get_json(silent=True) or {}
    limit = int(data.get("limit") or 200)
    res = reconcile_latest(limit=limit)
    return jsonify(res), 200
