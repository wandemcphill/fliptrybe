from __future__ import annotations

from datetime import datetime

from app.extensions import db
from app.models import NotificationQueue


def _enqueue(channel: str, to: str, message: str, reference: str = "") -> dict:
    q = NotificationQueue(
        channel=channel,
        to=(to or "").strip(),
        message=message,
        status="queued",
        reference=reference or None,
        attempt_count=0,
        max_attempts=5,
        next_attempt_at=datetime.utcnow(),
    )
    db.session.add(q)
    db.session.commit()
    return {"ok": True, "id": int(q.id)}


def enqueue_sms(to: str, message: str, reference: str = "") -> dict:
    return _enqueue("sms", to, message, reference)


def enqueue_whatsapp(to: str, message: str, reference: str = "") -> dict:
    return _enqueue("whatsapp", to, message, reference)


def enqueue_in_app(to_user_id: int, message: str, reference: str = "") -> dict:
    return _enqueue("in_app", str(int(to_user_id)), message, reference)
