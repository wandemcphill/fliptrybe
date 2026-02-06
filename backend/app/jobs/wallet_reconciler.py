from __future__ import annotations

import json
from datetime import datetime

from app.extensions import db
from sqlalchemy import func
from app.models import Wallet, WalletTxn, AuditLog


def _sum_ledger(wallet_id: int) -> float:
    credits = db.session.query(func.coalesce(func.sum(WalletTxn.amount), 0.0)).filter(
        WalletTxn.wallet_id == int(wallet_id),
        WalletTxn.direction == "credit",
    ).scalar() or 0.0
    debits = db.session.query(func.coalesce(func.sum(WalletTxn.amount), 0.0)).filter(
        WalletTxn.wallet_id == int(wallet_id),
        WalletTxn.direction == "debit",
    ).scalar() or 0.0
    return float(credits) - float(debits)


def reconcile_wallets(*, limit: int = 500, tolerance: float = 0.01) -> dict:
    """Detect wallet anomalies (ledger vs stored balance).

    This does NOT auto-correct balances. It logs anomalies into AuditLog so they are visible.
    """
    checked = 0
    anomalies = 0
    now = datetime.utcnow()

    wallets = Wallet.query.order_by(Wallet.id.asc()).limit(int(limit)).all()

    for w in wallets:
        checked += 1
        try:
            computed = _sum_ledger(int(w.id))
            stored = float(w.balance or 0.0)
            reserved = float(w.reserved_balance or 0.0)

            issues = []
            if abs(computed - stored) > float(tolerance):
                issues.append("ledger_mismatch")
            if reserved < -0.0001:
                issues.append("negative_reserved")
            if reserved - stored > float(tolerance):
                issues.append("reserved_exceeds_balance")

            if not issues:
                continue

            anomalies += 1
            meta = {
                "issues": issues,
                "wallet_id": int(w.id),
                "user_id": int(w.user_id),
                "computed_balance": round(computed, 4),
                "stored_balance": round(stored, 4),
                "reserved_balance": round(reserved, 4),
                "currency": w.currency or "NGN",
                "at": now.isoformat(),
            }
            log = AuditLog(
                actor_user_id=None,
                action="wallet_anomaly",
                target_type="wallet",
                target_id=int(w.id),
                meta=json.dumps(meta),
                created_at=now,
            )
            db.session.add(log)
            db.session.commit()
        except Exception:
            db.session.rollback()

    return {"checked": checked, "anomalies": anomalies}
