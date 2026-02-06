"""Wallet compatibility helpers.

Some legacy segments import `debit_wallet(...)` / `credit_wallet(...)`.
This implementation uses the Wallet + Transaction tables.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.extensions import db
from app.models import Wallet, Transaction, User


def _get_or_create_wallet(user_id: int) -> Wallet:
    w = Wallet.query.filter_by(user_id=user_id).first()
    if w:
        return w
    w = Wallet(user_id=user_id, balance=0.0)
    db.session.add(w)
    db.session.commit()
    return w


def debit_wallet(user_id: int, amount: float, *, reason: str = "wallet_debit") -> None:
    if amount is None or amount <= 0:
        raise ValueError("amount must be > 0")

    user: Optional[User] = User.query.get(user_id)
    if not user:
        raise ValueError("user not found")

    w = _get_or_create_wallet(user.id)
    if (w.balance or 0.0) < amount:
        raise ValueError("insufficient wallet balance")

    w.balance = float(w.balance or 0.0) - float(amount)

    tx = Transaction(
        wallet_id=w.id,
        amount=-abs(float(amount)),
        gross_amount=float(amount),
        net_amount=float(amount),
        commission_total=0.0,
        purpose="debit",
        direction="debit",
        reference=f"{reason}:{datetime.utcnow().isoformat()}",
        created_at=datetime.utcnow(),
    )

    db.session.add(tx)
    db.session.commit()


def credit_wallet(user_id: int, amount: float, *, reason: str = "wallet_credit") -> None:
    if amount is None or amount <= 0:
        raise ValueError("amount must be > 0")

    user: Optional[User] = User.query.get(user_id)
    if not user:
        raise ValueError("user not found")

    w = _get_or_create_wallet(user.id)
    w.balance = float(w.balance or 0.0) + float(amount)

    tx = Transaction(
        wallet_id=w.id,
        amount=abs(float(amount)),
        gross_amount=float(amount),
        net_amount=float(amount),
        commission_total=0.0,
        purpose="credit",
        direction="credit",
        reference=f"{reason}:{datetime.utcnow().isoformat()}",
        created_at=datetime.utcnow(),
    )

    db.session.add(tx)
    db.session.commit()
