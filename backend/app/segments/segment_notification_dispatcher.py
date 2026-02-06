from __future__ import annotations

from datetime import datetime
from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import User, Notification
from app.utils.jwt_utils import decode_token
from app.utils.notify import mark_sent, mark_failed

dispatcher_bp = Blueprint("dispatcher_bp", __name__, url_prefix="/api/admin")

_INIT_DONE = False


@dispatcher_bp.before_app_request
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
        if int(u.id or 0) == 1:
            return True
    except Exception:
        pass
    return (u.role or "").strip().lower() == "admin"


@dispatcher_bp.post("/notifications/process")
def process_queue():
    """Process queued notifications.

    - SMS/WhatsApp are processed via the NotificationQueue autopilot runner.
    - In-app notifications are marked as sent (since delivery is local).
    """
    user = _current_user()
    if not _is_admin(user):
        return jsonify({"message": "Forbidden"}), 403

    raw_limit = (request.args.get("limit") or "").strip()
    try:
        limit = int(raw_limit) if raw_limit else 50
    except Exception:
        limit = 50
    if limit < 1:
        limit = 50
    if limit > 200:
        limit = 200

    # 1) Process outbound (sms/whatsapp) queue
    from app.utils.autopilot import process_notification_queue
    q_result = process_notification_queue(max_items=limit)

    # 2) Mark in-app notifications as delivered
    rows = Notification.query.filter_by(status="queued", channel="in_app").order_by(Notification.created_at.asc()).limit(limit).all()
    sent = 0
    failed = 0
    for n in rows:
        try:
            mark_sent(n, provider_ref="local:in_app")
            sent += 1
        except Exception:
            mark_failed(n, provider_ref="local:fail")
            failed += 1

    try:
        db.session.commit()
        return jsonify({
            "ok": True,
            "outbound_queue": q_result,
            "in_app_processed": len(rows),
            "in_app_sent": sent,
            "in_app_failed": failed,
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Process failed", "error": str(e)}), 500
