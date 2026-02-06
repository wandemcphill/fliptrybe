from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import User, CommissionRule
from app.utils.jwt_utils import decode_token

commission_bp = Blueprint("commission_bp", __name__, url_prefix="/api/admin/commission")

_INIT = False


@commission_bp.before_app_request
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


def _is_admin(u: User | None) -> bool:
    if not u:
        return False
    try:
        if int(u.id or 0) == 1:
            return True
    except Exception:
        pass
    try:
        return "admin" in (u.email or "").lower()
    except Exception:
        return False


@commission_bp.get("")
def list_rules():
    u = _current_user()
    if not _is_admin(u):
        return jsonify([]), 200

    kind = (request.args.get("kind") or "").strip()
    state = (request.args.get("state") or "").strip()
    category = (request.args.get("category") or "").strip()

    q = CommissionRule.query.filter_by(is_active=True)
    if kind:
        q = q.filter(CommissionRule.kind.ilike(kind))
    if state:
        q = q.filter(CommissionRule.state.ilike(state))
    if category:
        q = q.filter(CommissionRule.category.ilike(category))

    rows = q.order_by(CommissionRule.kind.asc(), CommissionRule.state.asc(), CommissionRule.category.asc()).all()
    return jsonify([r.to_dict() for r in rows]), 200


@commission_bp.post("")
def upsert_rule():
    u = _current_user()
    if not _is_admin(u):
        return jsonify({"message": "Forbidden"}), 403

    payload = request.get_json(silent=True) or {}

    kind = (payload.get("kind") or "").strip()
    if not kind:
        return jsonify({"message": "kind is required"}), 400

    state = (payload.get("state") or "").strip()
    category = (payload.get("category") or "").strip()

    raw_rate = payload.get("rate")
    try:
        rate = float(raw_rate)
    except Exception:
        rate = 0.0

    if rate < 0:
        rate = 0.0

    # Find existing rule (kind+state+category)
    q = CommissionRule.query.filter_by(kind=kind, is_active=True)
    q = q.filter(CommissionRule.state == (state or None), CommissionRule.category == (category or None))
    r = q.first()
    if not r:
        r = CommissionRule(kind=kind, state=state or None, category=category or None)

    r.rate = rate
    r.updated_at = datetime.utcnow()
    r.is_active = True

    try:
        db.session.add(r)
        db.session.commit()
        return jsonify({"ok": True, "rule": r.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed", "error": str(e)}), 500


@commission_bp.post("/<int:rule_id>/disable")
def disable_rule(rule_id: int):
    u = _current_user()
    if not _is_admin(u):
        return jsonify({"message": "Forbidden"}), 403

    r = CommissionRule.query.get(rule_id)
    if not r:
        return jsonify({"message": "Not found"}), 404

    r.is_active = False
    r.updated_at = datetime.utcnow()

    try:
        db.session.add(r)
        db.session.commit()
        return jsonify({"ok": True, "rule": r.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed", "error": str(e)}), 500
