from __future__ import annotations

from datetime import datetime

from app.extensions import db
from app.models import InspectorBond, BondEvent


REQUIRED_BY_TIER = {
    "BRONZE": 5000.0,
    "SILVER": 3500.0,
    "GOLD": 2000.0,
    "PLATINUM": 1000.0,
}


def _now() -> datetime:
    return datetime.utcnow()


def required_amount_for_tier(tier: str | None) -> float:
    t = (tier or "BRONZE").strip().upper()
    return float(REQUIRED_BY_TIER.get(t, REQUIRED_BY_TIER["BRONZE"]))


def _normalize_amount(value) -> float:
    try:
        amt = float(value or 0.0)
    except Exception:
        amt = 0.0
    if amt < 0:
        amt = 0.0
    return float(amt)


def _update_status(bond: InspectorBond) -> None:
    required = float(bond.bond_required_amount or 0.0)
    available = float(bond.bond_available_amount or 0.0)
    if available >= required:
        bond.status = "ACTIVE"
    else:
        bond.status = "UNDERFUNDED"
    bond.updated_at = _now()


def _event_exists(inspector_user_id: int, event_type: str, reference_type: str | None, reference_id: int | None) -> bool:
    if reference_type is None or reference_id is None:
        return False
    row = BondEvent.query.filter_by(
        inspector_user_id=int(inspector_user_id),
        event_type=event_type,
        reference_type=reference_type,
        reference_id=int(reference_id),
    ).first()
    return row is not None


def _record_event(
    inspector_user_id: int,
    event_type: str,
    amount: float,
    reference_type: str | None = None,
    reference_id: int | None = None,
    note: str | None = None,
) -> BondEvent:
    ev = BondEvent(
        inspector_user_id=int(inspector_user_id),
        event_type=event_type,
        amount=_normalize_amount(amount),
        reference_type=(reference_type or None),
        reference_id=int(reference_id) if reference_id is not None else None,
        note=(note or "")[:400] if note else None,
    )
    db.session.add(ev)
    return ev


def get_or_create_bond(inspector_user_id: int, *, tier: str | None = None) -> InspectorBond:
    bond = InspectorBond.query.filter_by(inspector_user_id=int(inspector_user_id)).first()
    if not bond:
        bond = InspectorBond(
            inspector_user_id=int(inspector_user_id),
            bond_currency="NGN",
            bond_required_amount=required_amount_for_tier(tier),
            bond_available_amount=0.0,
            bond_reserved_amount=0.0,
            status="UNDERFUNDED",
            created_at=_now(),
            updated_at=_now(),
        )
        db.session.add(bond)
        db.session.commit()
        return bond

    if tier:
        new_required = required_amount_for_tier(tier)
        if float(bond.bond_required_amount or 0.0) != float(new_required):
            bond.bond_required_amount = new_required
            _update_status(bond)
            db.session.add(bond)
            db.session.commit()
    return bond


def refresh_bond_required_for_tier(inspector_user_id: int, tier: str | None) -> InspectorBond:
    bond = get_or_create_bond(int(inspector_user_id), tier=tier)
    new_required = required_amount_for_tier(tier)
    if float(bond.bond_required_amount or 0.0) != float(new_required):
        bond.bond_required_amount = new_required
    _update_status(bond)
    db.session.add(bond)
    db.session.commit()
    return bond


def can_cover_required(bond: InspectorBond) -> bool:
    required = float(bond.bond_required_amount or 0.0)
    available = float(bond.bond_available_amount or 0.0)
    return available >= required and (bond.status or "") == "ACTIVE"


def topup_bond(inspector_user_id: int, amount: float, note: str | None = None) -> InspectorBond:
    bond = get_or_create_bond(int(inspector_user_id))
    amt = _normalize_amount(amount)
    if amt <= 0:
        return bond
    bond.bond_available_amount = float(bond.bond_available_amount or 0.0) + amt
    bond.last_topup_at = _now()
    _update_status(bond)
    _record_event(inspector_user_id, "TOPUP", amt, reference_type=None, reference_id=None, note=note)
    db.session.add(bond)
    db.session.commit()
    return bond


def reserve_bond(
    inspector_user_id: int,
    amount: float,
    *,
    reference_type: str | None = None,
    reference_id: int | None = None,
    note: str | None = None,
) -> bool:
    if _event_exists(int(inspector_user_id), "RESERVE", reference_type, reference_id):
        return True
    bond = get_or_create_bond(int(inspector_user_id))
    amt = _normalize_amount(amount)
    if amt <= 0:
        return False
    available = float(bond.bond_available_amount or 0.0)
    if available < amt:
        _update_status(bond)
        db.session.add(bond)
        db.session.commit()
        return False
    bond.bond_available_amount = available - amt
    bond.bond_reserved_amount = float(bond.bond_reserved_amount or 0.0) + amt
    _update_status(bond)
    _record_event(inspector_user_id, "RESERVE", amt, reference_type=reference_type, reference_id=reference_id, note=note)
    db.session.add(bond)
    db.session.commit()
    return True


def release_bond(
    inspector_user_id: int,
    amount: float,
    *,
    reference_type: str | None = None,
    reference_id: int | None = None,
    note: str | None = None,
) -> bool:
    if _event_exists(int(inspector_user_id), "RELEASE", reference_type, reference_id):
        return True
    bond = get_or_create_bond(int(inspector_user_id))
    amt = _normalize_amount(amount)
    if amt <= 0:
        return False
    reserved = float(bond.bond_reserved_amount or 0.0)
    if reserved < amt:
        amt = reserved
    if amt <= 0:
        return False
    bond.bond_reserved_amount = reserved - amt
    bond.bond_available_amount = float(bond.bond_available_amount or 0.0) + amt
    _update_status(bond)
    _record_event(inspector_user_id, "RELEASE", amt, reference_type=reference_type, reference_id=reference_id, note=note)
    db.session.add(bond)
    db.session.commit()
    return True


def slash_bond(
    inspector_user_id: int,
    amount: float,
    *,
    reference_type: str | None = None,
    reference_id: int | None = None,
    note: str | None = None,
) -> bool:
    if _event_exists(int(inspector_user_id), "SLASH", reference_type, reference_id):
        return True
    bond = get_or_create_bond(int(inspector_user_id))
    amt = _normalize_amount(amount)
    if amt <= 0:
        return False

    reserved = float(bond.bond_reserved_amount or 0.0)
    available = float(bond.bond_available_amount or 0.0)

    use_reserved = min(reserved, amt)
    bond.bond_reserved_amount = reserved - use_reserved
    remaining = amt - use_reserved
    if remaining > 0:
        bond.bond_available_amount = max(0.0, available - remaining)

    bond.last_slash_at = _now()
    _update_status(bond)
    _record_event(inspector_user_id, "SLASH", amt, reference_type=reference_type, reference_id=reference_id, note=note)
    db.session.add(bond)
    db.session.commit()
    return True


def _reserve_amount_for_inspection(inspector_user_id: int, order_id: int) -> float:
    rows = BondEvent.query.filter_by(
        inspector_user_id=int(inspector_user_id),
        event_type="RESERVE",
        reference_type="INSPECTION",
        reference_id=int(order_id),
    ).all()
    total = 0.0
    for r in rows:
        total += float(r.amount or 0.0)
    return float(total)


def reserve_for_inspection(inspector_user_id: int, order_id: int, amount: float) -> bool:
    return reserve_bond(
        inspector_user_id,
        amount,
        reference_type="INSPECTION",
        reference_id=int(order_id),
        note=f"Reserve for inspection order {int(order_id)}",
    )


def release_for_inspection(inspector_user_id: int, order_id: int) -> bool:
    if _event_exists(int(inspector_user_id), "RELEASE", "INSPECTION", int(order_id)):
        return True
    amount = _reserve_amount_for_inspection(int(inspector_user_id), int(order_id))
    if amount <= 0:
        return False
    return release_bond(
        inspector_user_id,
        amount,
        reference_type="INSPECTION",
        reference_id=int(order_id),
        note=f"Release reserve for inspection order {int(order_id)}",
    )


def slash_for_audit(inspector_user_id: int, audit_id: int, order_id: int, *, tier: str | None = None) -> bool:
    if _event_exists(int(inspector_user_id), "SLASH", "AUDIT", int(audit_id)):
        return True
    amount = _reserve_amount_for_inspection(int(inspector_user_id), int(order_id))
    if amount <= 0:
        amount = required_amount_for_tier(tier)
    return slash_bond(
        inspector_user_id,
        amount,
        reference_type="AUDIT",
        reference_id=int(audit_id),
        note=f"Slash after audit overturned (order {int(order_id)})",
    )
