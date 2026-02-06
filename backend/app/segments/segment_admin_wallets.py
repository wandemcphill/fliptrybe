from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import User, AuditLog
from app.utils.jwt_utils import decode_token
from app.jobs.wallet_reconciler import reconcile_wallets

admin_wallets_bp = Blueprint("admin_wallets_bp", __name__, url_prefix="/api/admin/wallets")

_INIT = False


@admin_wallets_bp.before_app_request
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


@admin_wallets_bp.post("/reconcile")
def run_reconcile():
    u = _current_user()
    if not _is_admin(u):
        return jsonify({"message": "Forbidden"}), 403
    try:
        limit = int((request.args.get("limit") or 500))
    except Exception:
        limit = 500
    res = reconcile_wallets(limit=limit, tolerance=0.01)
    return jsonify({"ok": True, "result": res}), 200


@admin_wallets_bp.get("/anomalies")
def list_anomalies():
    u = _current_user()
    if not _is_admin(u):
        return jsonify({"message": "Forbidden"}), 403
    try:
        limit = int((request.args.get("limit") or 50))
    except Exception:
        limit = 50
    rows = (
        AuditLog.query
        .filter(AuditLog.action == "wallet_anomaly")
        .order_by(AuditLog.created_at.desc())
        .limit(max(1, min(limit, 200)))
        .all()
    )
    return jsonify({"ok": True, "items": [r.to_dict() for r in rows]}), 200
