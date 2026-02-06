from __future__ import annotations

from datetime import datetime

from app.extensions import db
from app.models import Wallet, WalletTxn
from sqlalchemy.exc import IntegrityError


def get_or_create_wallet(user_id: int) -> Wallet:
    w = Wallet.query.filter_by(user_id=user_id).first()
    if w:
        return w
    w = Wallet(user_id=user_id, balance=0.0, currency="NGN")
    try:
        db.session.add(w)
        db.session.commit()
        return w
    except IntegrityError:
        db.session.rollback()
        w = Wallet.query.filter_by(user_id=user_id).first()
        if w:
            return w
        raise


def post_txn(
    *,
    user_id: int,
    direction: str,
    amount: float,
    kind: str,
    reference: str,
    note: str,
    idempotency_key: str | None = None,
) -> WalletTxn | None:
    """Idempotent wallet posting: one txn per idempotency_key (or per user/kind/reference/direction)."""
    w = get_or_create_wallet(user_id)
    key = (idempotency_key or f"{int(user_id)}:{kind}:{direction}:{reference}")[:160]
    existing = WalletTxn.query.filter_by(idempotency_key=key).first()
    if not existing:
        existing = WalletTxn.query.filter_by(user_id=user_id, kind=kind, reference=reference, direction=direction).first()
    if existing:
        return existing

    amt = float(amount or 0.0)
    if amt <= 0:
        return None

    if direction == "credit" and reference:
        try:
            from app.utils.moneybox import autosave_from_commission
            sweep = autosave_from_commission(user_id=int(user_id), amount=float(amt), kind=str(kind), reference=str(reference))
            if sweep and sweep > 0:
                amt = max(0.0, float(amt) - float(sweep))
        except Exception:
            pass

    txn = WalletTxn(
        wallet_id=w.id,
        user_id=user_id,
        direction=direction,
        amount=amt,
        kind=kind,
        reference=reference,
        idempotency_key=key,
        note=(note or "")[:240],
    )

    if direction == "credit":
        w.balance = float(w.balance or 0.0) + amt
    elif direction == "debit":
        # Enforce non-negative and respect reserved balance.
        current = float(w.balance or 0.0)
        reserved = float(getattr(w, "reserved_balance", 0.0) or 0.0)
        available = current - reserved
        if amt > available:
            # Insufficient available funds: do not create txn.
            return None
        w.balance = current - amt
    w.updated_at = datetime.utcnow()

    try:
        db.session.add(txn)
        db.session.add(w)
        db.session.commit()
        return txn
    except Exception:
        db.session.rollback()
        existing = WalletTxn.query.filter_by(idempotency_key=key).first()
        if existing:
            return existing
        return None


def reserve_funds(user_id: int, amount: float) -> bool:
    """Move amount from available into reserved (no ledger txn)."""
    w = get_or_create_wallet(int(user_id))
    try:
        amt = float(amount or 0.0)
    except Exception:
        return False
    if amt <= 0:
        return False
    try:
        available = float(w.balance or 0.0) - float(getattr(w, "reserved_balance", 0.0) or 0.0)
        if available < amt:
            return False
        w.reserved_balance = float(getattr(w, "reserved_balance", 0.0) or 0.0) + amt
        db.session.add(w)
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False


def release_reserved(user_id: int, amount: float) -> bool:
    """Release reserved amount back to available."""
    w = get_or_create_wallet(int(user_id))
    try:
        amt = float(amount or 0.0)
    except Exception:
        return False
    if amt <= 0:
        return False
    try:
        rb = float(getattr(w, "reserved_balance", 0.0) or 0.0)
        w.reserved_balance = max(0.0, rb - amt)
        db.session.add(w)
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False
