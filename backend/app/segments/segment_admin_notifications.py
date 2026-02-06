from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import User, Notification
from app.utils.jwt_utils import decode_token
from app.utils.notify import queue_in_app, queue_sms, queue_whatsapp, mark_sent

admin_notify_bp = Blueprint("admin_notify_bp", __name__, url_prefix="/api/admin")

_INIT_DONE = False


@admin_notify_bp.before_app_request
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


def _current_user():
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
        user_id = int(sub)
    except Exception:
        return None
    return User.query.get(user_id)


def _is_admin(u: User | None) -> bool:
    if not u:
        return False
    try:
        return int(u.id or 0) == 1
    except Exception:
        return False


@admin_notify_bp.post("/notifications/broadcast")
def broadcast():
    """Broadcast notification to many users.
    Filters supported: state/city via merchant_profiles (best-effort).
    Channels: in_app|sms|whatsapp
    """
    user = _current_user()
    if not _is_admin(user):
        return jsonify({"message": "Forbidden"}), 403

    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "FlipTrybe").strip()
    message = (payload.get("message") or "").strip()
    channel = (payload.get("channel") or "in_app").strip().lower()
    state = (payload.get("state") or "").strip()
    city = (payload.get("city") or "").strip()

    if not message:
        return jsonify({"message": "message is required"}), 400

    # Best-effort targeting: if merchant_profiles exists, join; else fallback to all users.
    user_ids: list[int] = []
    try:
        from app.models.merchant import MerchantProfile  # local import safe
        q = MerchantProfile.query
        if state:
            q = q.filter(MerchantProfile.state.ilike(state))
        if city:
            q = q.filter(MerchantProfile.city.ilike(city))
        user_ids = [int(x.user_id) for x in q.all()]
    except Exception:
        user_ids = []

    if not user_ids:
        user_ids = [int(u.id) for u in User.query.limit(500).all()]

    created = []
    for uid in user_ids:
        if channel == "sms":
            n = queue_sms(uid, title, message, provider="stub", meta={"broadcast": True, "state": state, "city": city})
        elif channel == "whatsapp":
            n = queue_whatsapp(uid, title, message, provider="stub", meta={"broadcast": True, "state": state, "city": city})
        else:
            n = queue_in_app(uid, title, message, meta={"broadcast": True, "state": state, "city": city})
        mark_sent(n, "stub:broadcast")
        created.append(n)

    try:
        db.session.commit()
        return jsonify({"ok": True, "sent": len(created)}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Broadcast failed", "error": str(e)}), 500
