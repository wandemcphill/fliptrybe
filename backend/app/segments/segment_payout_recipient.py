from __future__ import annotations

import json
from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import User, PayoutRecipient, AuditLog
from app.utils.jwt_utils import decode_token

recipient_bp = Blueprint("recipient_bp", __name__, url_prefix="/api/payout/recipient")

_INIT = False


@recipient_bp.before_app_request
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


@recipient_bp.get("")
def get_recipient():
    u = _current_user()
    if not u:
        return jsonify({"message": "Unauthorized"}), 401
    row = PayoutRecipient.query.filter_by(user_id=int(u.id)).first()
    return jsonify({"ok": True, "recipient": row.to_dict() if row else None}), 200


@recipient_bp.post("")
def set_recipient():
    u = _current_user()
    if not u:
        return jsonify({"message": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    provider = (data.get("provider") or "paystack").strip()
    recipient_code = (data.get("recipient_code") or "").strip()
    if not recipient_code:
        return jsonify({"message": "recipient_code is required"}), 400

    row = PayoutRecipient.query.filter_by(user_id=int(u.id)).first()
    if row:
        row.provider = provider
        row.recipient_code = recipient_code
    else:
        row = PayoutRecipient(user_id=int(u.id), provider=provider, recipient_code=recipient_code)
        db.session.add(row)

    try:
        db.session.add(AuditLog(actor_user_id=int(u.id), action="recipient_set", target_type="recipient", target_id=None, meta=json.dumps({"provider": provider})))
        db.session.commit()
    except Exception:
        db.session.rollback()
        try:
            db.session.add(row)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({"message": "Failed"}), 500

    return jsonify({"ok": True, "recipient": row.to_dict()}), 200
