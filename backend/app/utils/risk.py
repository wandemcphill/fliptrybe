from __future__ import annotations

from datetime import datetime, timedelta

from app.extensions import db
from app.models import WalletTxn, User


def payout_limit_for_user(u: User) -> float:
    tier = int(getattr(u, "kyc_tier", 0) or 0)
    # NGN caps per day (demo): 0=50k, 1=200k, 2=1m
    if tier <= 0:
        return 50_000.0
    if tier == 1:
        return 200_000.0
    return 1_000_000.0


def paid_out_today(user_id: int) -> float:
    now = datetime.utcnow()
    start = datetime(now.year, now.month, now.day)
    rows = (
        WalletTxn.query
        .filter(WalletTxn.user_id == int(user_id))
        .filter(WalletTxn.kind == "payout")
        .filter(WalletTxn.direction == "debit")
        .filter(WalletTxn.created_at >= start)
        .all()
    )
    return float(sum([float(r.amount or 0.0) for r in rows]) or 0.0)


def can_request_payout(u: User, amount: float) -> tuple[bool, str]:
    try:
        amt = float(amount or 0.0)
    except Exception:
        return False, "Invalid amount"
    if amt <= 0:
        return False, "Invalid amount"
    limit = payout_limit_for_user(u)
    used = paid_out_today(int(u.id))
    if used + amt > limit:
        return False, f"Payout limit reached for today (tier {int(getattr(u,'kyc_tier',0) or 0)})"
    return True, ""


def txn_velocity_ok(user_id: int, window_minutes: int = 10, max_txns: int = 25) -> tuple[bool, str]:
    since = datetime.utcnow() - timedelta(minutes=window_minutes)
    cnt = (
        db.session.query(db.func.count(WalletTxn.id))
        .filter(WalletTxn.user_id == int(user_id))
        .filter(WalletTxn.created_at >= since)
        .scalar()
    )
    cnt = int(cnt or 0)
    if cnt > max_txns:
        return False, "High activity detected; try again shortly"
    return True, ""


PAYOUT_COOLDOWN_MINUTES = 30

def payout_cooldown_ok(user_id: int) -> tuple[bool, str]:
    from datetime import datetime, timedelta
    from app.models import PayoutRequest
    row = (
        PayoutRequest.query
        .filter(PayoutRequest.user_id == int(user_id))
        .order_by(PayoutRequest.created_at.desc())
        .first()
    )
    if not row:
        return True, ""
    if datetime.utcnow() - row.created_at < timedelta(minutes=PAYOUT_COOLDOWN_MINUTES):
        return False, f"Please wait {PAYOUT_COOLDOWN_MINUTES} minutes between payout requests"
    return True, ""
