from __future__ import annotations

from datetime import datetime, timedelta

from app.extensions import db
import json

from app.models import Order, AuditLog, User, Listing, MerchantProfile, OrderEvent, EscrowUnlock
from app.utils.wallets import post_txn
from app.utils.commission import compute_commission, RATES
import os


def _now():
    return datetime.utcnow()


def _platform_user_id() -> int:
    raw = (os.getenv("PLATFORM_USER_ID") or "").strip()
    if raw.isdigit():
        return int(raw)
    try:
        admin = User.query.filter_by(role="admin").order_by(User.id.asc()).first()
        if admin:
            return int(admin.id)
    except Exception:
        pass
    return 1


def _seller_role(user_id: int | None) -> str:
    if not user_id:
        return "buyer"
    try:
        u = User.query.get(int(user_id))
    except Exception:
        u = None
    if not u:
        return "buyer"
    role = (getattr(u, "role", "") or "buyer").strip().lower()
    if role in ("driver", "inspector"):
        return "merchant"
    return role


def _is_top_tier(merchant_id: int | None) -> bool:
    if not merchant_id:
        return False
    try:
        mp = MerchantProfile.query.filter_by(user_id=int(merchant_id)).first()
        if mp:
            return bool(getattr(mp, "is_top_tier", False))
    except Exception:
        pass
    return False


def _credit_seller(order: Order, listing: Listing | None, ref: str, order_amount: float) -> None:
    seller_role = _seller_role(order.merchant_id)
    if order_amount <= 0:
        return

    if seller_role == "merchant":
        base_price = float(getattr(listing, "base_price", 0.0) or 0.0) if listing else 0.0
        if base_price <= 0.0:
            try:
                base_price = float(order_amount) / 1.03 if order_amount > 0 else 0.0
            except Exception:
                base_price = float(order_amount or 0.0)
        platform_fee = float(getattr(listing, "platform_fee", 0.0) or 0.0) if listing else 0.0
        if platform_fee <= 0.0 and base_price > 0:
            platform_fee = round(base_price * 0.03, 2)
        final_price = float(getattr(listing, "final_price", 0.0) or 0.0) if listing else 0.0
        if final_price <= 0.0:
            final_price = round(base_price + platform_fee, 2)
        if order_amount > 0 and abs(final_price - order_amount) > 0.05:
            platform_fee = round(max(order_amount - base_price, 0.0), 2)
            final_price = round(base_price + platform_fee, 2)

        if base_price > 0:
            post_txn(
                user_id=int(order.merchant_id),
                direction="credit",
                amount=float(base_price),
                kind="order_sale",
                reference=ref,
                note=f"Order sale (base) for order #{int(order.id)}",
            )

        if platform_fee > 0:
            if _is_top_tier(order.merchant_id):
                incentive = round(platform_fee * (11.0 / 13.0), 2)
                platform_share = round(platform_fee - incentive, 2)
                if incentive > 0:
                    post_txn(
                        user_id=int(order.merchant_id),
                        direction="credit",
                        amount=float(incentive),
                        kind="top_tier_incentive",
                        reference=ref,
                        note=f"Top-tier incentive for order #{int(order.id)}",
                    )
                if platform_share > 0:
                    post_txn(
                        user_id=_platform_user_id(),
                        direction="credit",
                        amount=float(platform_share),
                        kind="platform_fee",
                        reference=ref,
                        note=f"Platform fee for order #{int(order.id)}",
                    )
            else:
                post_txn(
                    user_id=_platform_user_id(),
                    direction="credit",
                    amount=float(platform_fee),
                    kind="platform_fee",
                    reference=ref,
                    note=f"Platform fee for order #{int(order.id)}",
                )
    else:
        commission_fee = compute_commission(order_amount, float(RATES.get("listing_sale", 0.05)))
        net_amount = round(float(order_amount) - float(commission_fee), 2)
        if net_amount > 0:
            post_txn(
                user_id=int(order.merchant_id),
                direction="credit",
                amount=float(net_amount),
                kind="order_sale",
                reference=ref,
                note=f"Order sale (net) for order #{int(order.id)}",
            )
        if commission_fee > 0:
            post_txn(
                user_id=_platform_user_id(),
                direction="credit",
                amount=float(commission_fee),
                kind="user_listing_commission",
                reference=ref,
                note=f"User listing commission for order #{int(order.id)}",
            )


def _credit_driver(order: Order, ref: str, delivery_fee: float) -> None:
    if delivery_fee <= 0 or not order.driver_id:
        return
    delivery_commission = compute_commission(delivery_fee, float(RATES.get("delivery", 0.10)))
    net_delivery = round(float(delivery_fee) - float(delivery_commission), 2)
    if net_delivery > 0:
        post_txn(
            user_id=int(order.driver_id),
            direction="credit",
            amount=float(net_delivery),
            kind="delivery_fee",
            reference=ref,
            note=f"Delivery fee (net) for order #{int(order.id)}",
        )
    if delivery_commission > 0:
        post_txn(
            user_id=_platform_user_id(),
            direction="credit",
            amount=float(delivery_commission),
            kind="delivery_commission",
            reference=ref,
            note=f"Delivery commission for order #{int(order.id)}",
        )


def _hold_order_into_escrow(order: Order) -> None:
    """Idempotently mark an order as HELD.

    IMPORTANT: This does not charge a card. It assumes payment already happened and
    we are now accounting internally.
    """
    if (order.escrow_status or "NONE") != "NONE":
        return
    order.escrow_status = "HELD"
    order.escrow_hold_amount = float(order.amount or 0.0) + float(order.delivery_fee or 0.0) + float(getattr(order, "inspection_fee", 0.0) or 0.0)
    order.escrow_held_at = _now()
    if order.inspection_required:
        order.release_condition = "INSPECTION_PASS"
    elif not (order.release_condition or "").strip():
        order.release_condition = "BUYER_CONFIRM"
    order.updated_at = _now()


def _release_escrow(order: Order) -> None:
    if (order.escrow_status or "NONE") != "HELD":
        return
    ref = f"order:{int(order.id)}"
    order_amount = float(order.amount or 0.0)
    delivery_fee = float(order.delivery_fee or 0.0)
    listing = None
    if order.listing_id:
        try:
            listing = Listing.query.get(int(order.listing_id))
        except Exception:
            listing = None

    _credit_seller(order, listing, ref, order_amount)
    _credit_driver(order, ref, delivery_fee)
    _settle_inspection_fee(order)

    order.escrow_status = "RELEASED"
    order.escrow_release_at = _now()
    order.updated_at = _now()
    _event_once(int(order.id), "escrow_released", "Escrow released")


def _refund_escrow(order: Order) -> None:
    if (order.escrow_status or "NONE") != "HELD":
        return
    amount = float(order.escrow_hold_amount or 0.0)
    if amount <= 0:
        order.escrow_status = "REFUNDED"
        order.escrow_refund_at = _now()
        return
    post_txn(
        user_id=int(order.buyer_id),
        direction="credit",
        amount=amount,
        kind="escrow_refund",
        reference=f"order:{int(order.id)}",
        note=f"Escrow refund for order #{int(order.id)}",
    )
    order.escrow_status = "REFUNDED"
    order.escrow_refund_at = _now()
    order.updated_at = _now()
    _event_once(int(order.id), "escrow_refunded", "Escrow refunded")


def _event_once(order_id: int, event: str, note: str = "") -> None:
    try:
        key = f"order:{int(order_id)}:{event}:system"
        existing = OrderEvent.query.filter_by(idempotency_key=key[:160]).first()
        if not existing:
            existing = OrderEvent.query.filter_by(order_id=int(order_id), event=event).first()
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
        db.session.commit()
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass


def _settle_inspection_fee(order: Order) -> None:
    inspection_fee = float(getattr(order, "inspection_fee", 0.0) or 0.0)
    if inspection_fee <= 0 or not order.inspector_id:
        return
    inspection_commission = compute_commission(inspection_fee, float(RATES.get("inspection", 0.10)))
    net_inspection = round(float(inspection_fee) - float(inspection_commission), 2)
    if net_inspection > 0:
        post_txn(
            user_id=int(order.inspector_id),
            direction="credit",
            amount=float(net_inspection),
            kind="inspection_fee",
            reference=f"inspection:{int(order.id)}",
            note=f"Inspection fee (net) for order #{int(order.id)}",
        )
    if inspection_commission > 0:
        post_txn(
            user_id=_platform_user_id(),
            direction="credit",
            amount=float(inspection_commission),
            kind="inspection_commission",
            reference=f"inspection:{int(order.id)}",
            note=f"Inspection commission for order #{int(order.id)}",
        )


def _inspection_unlock_ready(order_id: int) -> bool:
    try:
        row = EscrowUnlock.query.filter_by(order_id=int(order_id), step="inspection_inspector").first()
        return bool(row and row.unlocked_at)
    except Exception:
        return False


def run_escrow_automation(*, limit: int = 500) -> dict:
    """Run escrow automation for HELD orders.

    Rules:
      - If inspection_outcome == PASS: release when release_condition allows.
      - If inspection_outcome in (FAIL, FRAUD): refund.
      - If inspection_outcome == PASS and release_condition == TIMEOUT: release after timeout.
      - Otherwise: do nothing.
    """

    processed = 0
    released = 0
    refunded = 0
    skipped = 0
    errors = 0

    rows = (
        Order.query.filter_by(escrow_status="HELD")
        .order_by(Order.id.asc())
        .limit(int(limit))
        .all()
    )

    for o in rows:
        processed += 1
        try:
            status = (o.status or "").strip().lower()
            if status in ("delivered", "completed", "closed") and (o.escrow_status or "NONE") == "HELD":
                o.escrow_status = "DISPUTED"
                o.escrow_disputed_at = _now()
                o.updated_at = _now()
                _event_once(int(o.id), "escrow_disputed", f"Escrow disputed due to status {status}")
                try:
                    db.session.add(
                        AuditLog(
                            actor_user_id=None,
                            action="escrow_violation",
                            target_type="order",
                            target_id=int(o.id),
                            meta=json.dumps({
                                "order_id": int(o.id),
                                "status": status,
                                "escrow_status": "HELD",
                                "ts": _now().isoformat(),
                            }),
                        )
                    )
                except Exception:
                    pass
                skipped += 1
                continue

            outcome = (o.inspection_outcome or "NONE").upper()
            cond = (o.release_condition or "INSPECTION_PASS").upper()

            # Refund is immediate on FAIL/FRAUD.
            if outcome in ("FAIL", "FRAUD"):
                _settle_inspection_fee(o)
                _refund_escrow(o)
                refunded += 1
                continue

            if outcome == "PASS":
                if cond == "INSPECTION_PASS":
                    if not _inspection_unlock_ready(int(o.id)):
                        skipped += 1
                        continue
                    _settle_inspection_fee(o)
                    _release_escrow(o)
                    released += 1
                    continue
                _settle_inspection_fee(o)
                if cond == "TIMEOUT":
                    held_at = o.escrow_held_at or o.created_at
                    timeout = timedelta(hours=int(o.release_timeout_hours or 48))
                    if held_at and _now() >= (held_at + timeout):
                        _release_escrow(o)
                        released += 1
                        continue
                # BUYER_CONFIRM / ADMIN are not auto.
                skipped += 1
                continue

            skipped += 1
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
        "released": released,
        "refunded": refunded,
        "skipped": skipped,
        "errors": errors,
        "ts": _now().isoformat(),
    }
