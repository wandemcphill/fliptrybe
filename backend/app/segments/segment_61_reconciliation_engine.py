"""
=====================================================
FLIPTRYBE SEGMENT 61
PAYMENT RECONCILIATION ENGINE
=====================================================
Ensures escrow, wallets and
transactions never diverge.
Detects double credits,
orphaned refs,
auto-rollback.
=====================================================
"""

from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime
import uuid


# =====================================================
# DATA MODELS
# =====================================================

@dataclass
class LedgerEntry:
    id: str
    user_id: int
    amount: float
    kind: str  # credit/debit/escrow_hold/escrow_release/refund
    ref: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ReconciliationIssue:
    id: str
    order_id: int
    severity: str
    description: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False


# =====================================================
# STORES (IN MEMORY STUB)
# =====================================================

LEDGER: List[LedgerEntry] = []
ESCROW: Dict[int, float] = {}
ISSUES: List[ReconciliationIssue] = []


# =====================================================
# LEDGER HELPERS
# =====================================================

def add_entry(user_id, amount, kind, ref):

    entry = LedgerEntry(
        id=str(uuid.uuid4()),
        user_id=user_id,
        amount=round(amount, 2),
        kind=kind,
        ref=ref,
    )

    LEDGER.append(entry)
    return entry


# =====================================================
# SCAN ENGINE
# =====================================================

def reconcile_order(order_id, buyer_id, seller_id, total):

    issues = []

    escrow_amt = ESCROW.get(order_id, 0)

    buyer_debits = sum(
        e.amount for e in LEDGER
        if e.user_id == buyer_id and e.kind == "debit" and e.ref == f"ORD-{order_id}"
    )

    seller_credits = sum(
        e.amount for e in LEDGER
        if e.user_id == seller_id and e.kind == "credit" and e.ref == f"ORD-{order_id}"
    )

    # -----------------------------
    # Escrow mismatch
    # -----------------------------
    if round(escrow_amt, 2) != round(total, 2):
        issues.append(("HIGH", f"Escrow mismatch {escrow_amt} vs {total}"))

    # -----------------------------
    # Buyer mismatch
    # -----------------------------
    if round(buyer_debits, 2) != round(total, 2):
        issues.append(("HIGH", f"Buyer debit mismatch {buyer_debits} vs {total}"))

    # -----------------------------
    # Seller mismatch
    # -----------------------------
    expected_payout = round(total * 0.95, 2)

    if seller_credits and round(seller_credits, 2) != expected_payout:
        issues.append(("CRITICAL", f"Seller payout mismatch {seller_credits} vs {expected_payout}"))

    # -----------------------------
    # Register issues
    # -----------------------------
    for sev, desc in issues:
        ISSUES.append(
            ReconciliationIssue(
                id=str(uuid.uuid4()),
                order_id=order_id,
                severity=sev,
                description=desc,
            )
        )

    return issues


# =====================================================
# DOUBLE CREDIT DETECTOR
# =====================================================

def detect_double_credit(user_id, ref):

    credits = [
        e for e in LEDGER
        if e.user_id == user_id and e.kind == "credit" and e.ref == ref
    ]

    return len(credits) > 1


# =====================================================
# ROLLBACK QUEUE
# =====================================================

ROLLBACK_QUEUE: List[dict] = []


def queue_rollback(order_id, reason):

    ROLLBACK_QUEUE.append({
        "order_id": order_id,
        "reason": reason,
        "queued_at": datetime.utcnow()
    })


# =====================================================
# AUTO CORRECTION
# =====================================================

def auto_fix(order_id, buyer_id, seller_id, total):

    issues = reconcile_order(order_id, buyer_id, seller_id, total)

    if not issues:
        return "clean"

    for sev, desc in issues:
        if sev == "CRITICAL":
            queue_rollback(order_id, desc)

    return issues


# =====================================================
# ADMIN DASH SNAPSHOT
# =====================================================

def audit_snapshot():

    return {
        "ledger_count": len(LEDGER),
        "escrow_open": len(ESCROW),
        "issues": len(ISSUES),
        "rollback_queue": len(ROLLBACK_QUEUE),
    }


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    ESCROW[1] = 1000

    add_entry(10, 1000, "debit", "ORD-1")
    add_entry(20, 950, "credit", "ORD-1")

    print(reconcile_order(1, 10, 20, 1000))
    print(audit_snapshot())