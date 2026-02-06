from __future__ import annotations

from flask import Blueprint, jsonify, request
from datetime import datetime

from app.extensions import db
from app.models import User, InspectorProfile, BondEvent, MoneyBoxAccount
from app.utils.jwt_utils import decode_token
from app.utils.bonding import get_or_create_bond, topup_bond, refresh_bond_required_for_tier
from app.utils.moneybox import liquidate_to_wallet


inspector_bonds_admin_bp = Blueprint("inspector_bonds_admin_bp", __name__, url_prefix="/api/admin/inspectors")

_INIT_DONE = False


@inspector_bonds_admin_bp.before_app_request
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


def _is_admin(u: User | None) -> bool:
    if not u:
        return False
    if (u.role or "").lower() == "admin":
        return True
    try:
        return int(u.id or 0) == 1
    except Exception:
        return False


@inspector_bonds_admin_bp.get("/<int:user_id>/bond")
def get_bond(user_id: int):
    u = _current_user()
    if not _is_admin(u):
        return jsonify({"message": "Forbidden"}), 403

    prof = InspectorProfile.query.filter_by(user_id=int(user_id)).first()
    if prof:
        bond = refresh_bond_required_for_tier(int(user_id), prof.reputation_tier)
    else:
        bond = get_or_create_bond(int(user_id))

    events = (
        BondEvent.query
        .filter_by(inspector_user_id=int(user_id))
        .order_by(BondEvent.created_at.desc())
        .limit(50)
        .all()
    )

    return jsonify({
        "ok": True,
        "bond": bond.to_dict(),
        "events": [e.to_dict() for e in events],
    }), 200


@inspector_bonds_admin_bp.post("/<int:user_id>/bond/topup")
def topup(user_id: int):
    u = _current_user()
    if not _is_admin(u):
        return jsonify({"message": "Forbidden"}), 403

    payload = request.get_json(silent=True) or {}
    try:
        amount = float(payload.get("amount") or 0.0)
    except Exception:
        amount = 0.0
    if amount <= 0:
        return jsonify({"message": "amount must be > 0"}), 400

    note = (payload.get("note") or "").strip()
    bond = topup_bond(int(user_id), amount, note=note)
    return jsonify({"ok": True, "bond": bond.to_dict()}), 200


@inspector_bonds_admin_bp.post("/<int:user_id>/suspend")
def suspend_inspector(user_id: int):
    u = _current_user()
    if not _is_admin(u):
        return jsonify({"message": "Forbidden"}), 403

    payload = request.get_json(silent=True) or {}
    active = payload.get("is_active")
    if active is None:
        active = False
    if isinstance(active, bool):
        is_active = active
    else:
        is_active = str(active).strip().lower() in ("1", "true", "yes", "y", "on")

    prof = InspectorProfile.query.filter_by(user_id=int(user_id)).first()
    if not prof:
        prof = InspectorProfile(user_id=int(user_id), is_active=bool(is_active))
    prof.is_active = bool(is_active)
    prof.updated_at = datetime.utcnow()

    try:
        db.session.add(prof)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed", "error": str(e)}), 500

    if not prof.is_active:
        try:
            acct = MoneyBoxAccount.query.filter_by(user_id=int(user_id)).first()
            if acct:
                liquidate_to_wallet(acct, reason="inspector_suspended", reference=f"inspector_suspended:{int(user_id)}")
        except Exception:
            pass

    return jsonify({"ok": True, "profile": prof.to_dict()}), 200
