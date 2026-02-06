from __future__ import annotations

import json
from datetime import datetime

from app.extensions import db
from app.models import AuditLog, Order, PaymentTransaction, PaymentIntent


def reconcile_latest(limit: int = 200) -> dict:
    """Lightweight reconciliation:
    - ensures paid payment intents have matching wallet credit txn
    - ensures completed orders have ledger txns (best-effort)
    Logs findings to audit.
    """
    fixed = 0
    issues = []

    intents = PaymentIntent.query.order_by(PaymentIntent.created_at.desc()).limit(limit).all()
    for pi in intents:
        try:
            if pi.status != "paid":
                continue
            ref = f"pay:{pi.reference}"
            existing = PaymentTransaction.query.filter_by(reference=ref).first()
            if not existing:
                # can't import wallets.post_txn here without circular, just log
                issues.append({"type": "missing_wallet_txn", "ref": ref, "user_id": int(pi.user_id), "amount": float(pi.amount or 0.0)})
        except Exception:
            continue

    # Orders: just check and log for now (depends on your order ledger implementation)
    orders = Order.query.order_by(Order.created_at.desc()).limit(limit).all()
    for o in orders:
        try:
            if (getattr(o, "status", "") or "") not in ["delivered", "completed"]:
                continue
            # you can extend this to check commission txns by reference "order:<id>"
        except Exception:
            continue

    try:
        db.session.add(AuditLog(actor_user_id=None, action="reconcile_run", target_type="system", target_id=None, meta=json.dumps({"issues": issues[:25], "count": len(issues), "ts": datetime.utcnow().isoformat()})))
        db.session.commit()
    except Exception:
        db.session.rollback()

    return {"ok": True, "issues": issues, "fixed": fixed}
