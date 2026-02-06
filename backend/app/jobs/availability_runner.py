from __future__ import annotations

from datetime import datetime

from app.extensions import db
from app.models import AvailabilityConfirmation, Order, Listing, OrderEvent
from app.jobs.escrow_runner import _refund_escrow


def _now():
    return datetime.utcnow()


def _event_once(order_id: int, event: str, note: str = "") -> None:
    try:
        key = f"order:{int(order_id)}:{event}:system"
        existing = OrderEvent.query.filter_by(idempotency_key=key[:160]).first()
        if existing:
            return
        row = OrderEvent(
            order_id=int(order_id),
            actor_user_id=None,
            event=event,
            note=note[:240],
            idempotency_key=key[:160],
        )
        db.session.add(row)
    except Exception:
        pass


def run_availability_timeouts(*, limit: int = 200) -> dict:
    now = _now()
    processed = 0
    expired = 0
    refunded = 0
    errors = 0

    rows = (
        AvailabilityConfirmation.query
        .filter_by(status="pending")
        .filter(AvailabilityConfirmation.deadline_at < now)
        .order_by(AvailabilityConfirmation.deadline_at.asc())
        .limit(int(limit))
        .all()
    )

    for conf in rows:
        processed += 1
        try:
            conf.status = "expired"
            conf.responded_at = now

            order = Order.query.get(int(conf.order_id))
            if order:
                order.status = "cancelled"
                order.updated_at = now
                if order.listing_id:
                    listing = Listing.query.get(int(order.listing_id))
                    if listing and hasattr(listing, "is_active"):
                        listing.is_active = True
                _refund_escrow(order)
                refunded += 1
                _event_once(int(order.id), "availability_expired", "Availability confirmation expired")

            expired += 1
        except Exception:
            errors += 1
            db.session.rollback()

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        errors += 1

    return {
        "ok": True,
        "processed": processed,
        "expired": expired,
        "refunded": refunded,
        "errors": errors,
        "ts": now.isoformat(),
    }
