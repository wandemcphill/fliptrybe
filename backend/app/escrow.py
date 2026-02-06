from __future__ import annotations

from datetime import datetime

from app.extensions import db
from app.models import Order, Listing, WalletTxn
from app.jobs.escrow_runner import _credit_seller, _credit_driver, _settle_inspection_fee, _event_once, _now


def _seller_paid(order: Order) -> bool:
    if float(order.amount or 0.0) <= 0:
        return True
    ref = f"order:{int(order.id)}"
    row = WalletTxn.query.filter_by(
        user_id=int(order.merchant_id),
        kind="order_sale",
        direction="credit",
        reference=ref,
    ).first()
    return bool(row)


def _driver_needed(order: Order) -> bool:
    if (order.fulfillment_mode or "unselected") != "delivery":
        return False
    if not order.driver_id:
        return False
    return float(order.delivery_fee or 0.0) > 0


def _driver_paid(order: Order) -> bool:
    if not _driver_needed(order):
        return True
    ref = f"order:{int(order.id)}"
    row = WalletTxn.query.filter_by(
        user_id=int(order.driver_id),
        kind="delivery_fee",
        direction="credit",
        reference=ref,
    ).first()
    return bool(row)


def _inspector_needed(order: Order) -> bool:
    return bool(order.inspection_required or (order.fulfillment_mode or "") == "inspection" or order.inspector_id)


def _inspector_paid(order: Order) -> bool:
    if not _inspector_needed(order):
        return True
    ref = f"inspection:{int(order.id)}"
    if not order.inspector_id:
        return False
    row = WalletTxn.query.filter_by(
        user_id=int(order.inspector_id),
        kind="inspection_fee",
        direction="credit",
        reference=ref,
    ).first()
    return bool(row)


def _maybe_finalize_escrow(order: Order) -> None:
    # Only auto-finalize for non-inspection flows.
    if _inspector_needed(order):
        return
    if _seller_paid(order) and _driver_paid(order):
        order.escrow_status = "RELEASED"
        order.escrow_release_at = _now()
        order.updated_at = _now()
        try:
            _event_once(int(order.id), "escrow_released", "Escrow released")
        except Exception:
            pass
        db.session.add(order)


def release_seller_payout(order: Order) -> None:
    listing = Listing.query.get(int(order.listing_id)) if order.listing_id else None
    ref = f"order:{int(order.id)}"
    _credit_seller(order, listing, ref, float(order.amount or 0.0))
    _maybe_finalize_escrow(order)


def release_driver_payout(order: Order) -> None:
    ref = f"order:{int(order.id)}"
    _credit_driver(order, ref, float(order.delivery_fee or 0.0))
    _maybe_finalize_escrow(order)


def release_inspector_payout(order: Order) -> None:
    _settle_inspection_fee(order)
    # Do not finalize escrow here; inspection flow is finalized by inspection outcome handling.
