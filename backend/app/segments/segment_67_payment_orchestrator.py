"""
=====================================================
FLIPTRYBE SEGMENT 67
PAYMENT ORCHESTRATION LAYER
=====================================================
Responsibilities:
1. Provider abstraction (Paystack, Flutterwave, Stripe)
2. Runtime switching
3. Retry scheduler
4. Fee engine
5. Settlement ledger
6. Reconciliation logic
7. Dispute hooks
8. Compliance signals
9. Export pipelines
10. Webhook routing
=====================================================
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import uuid
import csv
import io


# =====================================================
# LEDGER MODELS
# =====================================================

@dataclass
class LedgerEntry:
    id: str
    order_id: int
    provider: str
    amount: float
    fee: float
    net_amount: float
    status: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DisputeSignal:
    id: str
    order_id: int
    reason: str
    provider: str
    opened_at: datetime = field(default_factory=datetime.utcnow)


# =====================================================
# STORES
# =====================================================

LEDGER: Dict[str, LedgerEntry] = {}
DISPUTES: Dict[str, DisputeSignal] = {}
RETRY_QUEUE: Dict[str, int] = {}


# =====================================================
# FEE ENGINE
# =====================================================

class FeeEngine:

    PLATFORM_RATE = 0.05

    @classmethod
    def compute(cls, amount: float):

        fee = round(amount * cls.PLATFORM_RATE, 2)
        return fee, amount - fee


# =====================================================
# PROVIDER INTERFACE
# =====================================================

class PaymentProvider(ABC):

    @abstractmethod
    def charge(self, order_id: int, amount: float):
        ...

    @abstractmethod
    def payout(self, order_id: int, amount: float):
        ...


# =====================================================
# PROVIDERS
# =====================================================

class PaystackProvider(PaymentProvider):

    name = "paystack"

    def charge(self, order_id: int, amount: float):

        ref = f"PSK-{uuid.uuid4()}"
        return {"reference": ref, "status": "pending"}

    def payout(self, order_id: int, amount: float):

        ref = f"PSK-OUT-{uuid.uuid4()}"
        return {"reference": ref, "status": "processing"}


class FlutterwaveProvider(PaymentProvider):

    name = "flutterwave"

    def charge(self, order_id: int, amount: float):

        ref = f"FLW-{uuid.uuid4()}"
        return {"reference": ref, "status": "pending"}

    def payout(self, order_id: int, amount: float):

        ref = f"FLW-OUT-{uuid.uuid4()}"
        return {"reference": ref, "status": "processing"}


# =====================================================
# REGISTRY
# =====================================================

PROVIDERS = {
    "paystack": PaystackProvider(),
    "flutterwave": FlutterwaveProvider(),
}


# =====================================================
# ORCHESTRATOR
# =====================================================

class PaymentOrchestrator:

    def __init__(self, default_provider="paystack"):

        self.default_provider = default_provider

    # --------------------------

    def charge(self, order_id: int, amount: float):

        provider = PROVIDERS[self.default_provider]

        fee, net = FeeEngine.compute(amount)

        response = provider.charge(order_id, amount)

        entry = LedgerEntry(
            id=str(uuid.uuid4()),
            order_id=order_id,
            provider=provider.name,
            amount=amount,
            fee=fee,
            net_amount=net,
            status=response["status"],
        )

        LEDGER[entry.id] = entry

        return entry

    # --------------------------

    def payout(self, order_id: int, amount: float):

        provider = PROVIDERS[self.default_provider]

        response = provider.payout(order_id, amount)

        entry = LedgerEntry(
            id=str(uuid.uuid4()),
            order_id=order_id,
            provider=provider.name,
            amount=amount,
            fee=0,
            net_amount=amount,
            status=response["status"],
        )

        LEDGER[entry.id] = entry

        return entry

    # --------------------------

    def retry_failed(self, ledger_id: str):

        entry = LEDGER.get(ledger_id)

        if not entry:
            raise ValueError("Ledger entry not found")

        RETRY_QUEUE[ledger_id] = RETRY_QUEUE.get(ledger_id, 0) + 1
        entry.status = "retrying"

    # --------------------------

    def reconcile(self, provider_refs: List[str]):

        reconciled = []

        for e in LEDGER.values():
            if e.id in provider_refs:
                e.status = "settled"
                reconciled.append(e.id)

        return reconciled

    # --------------------------

    def raise_dispute(self, order_id: int, reason: str):

        d = DisputeSignal(
            id=str(uuid.uuid4()),
            order_id=order_id,
            reason=reason,
            provider=self.default_provider,
        )

        DISPUTES[d.id] = d
        return d

    # --------------------------

    def export_ledger_csv(self):

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "id", "order_id", "provider",
            "amount", "fee", "net",
            "status", "created_at",
        ])

        for e in LEDGER.values():
            writer.writerow([
                e.id,
                e.order_id,
                e.provider,
                e.amount,
                e.fee,
                e.net_amount,
                e.status,
                e.created_at.isoformat(),
            ])

        return output.getvalue()


# =====================================================
# WEBHOOK ROUTER
# =====================================================

def route_provider_webhook(provider: str, payload: dict):

    ref = payload.get("reference")

    for e in LEDGER.values():
        if e.id == ref:
            e.status = payload.get("status", e.status)


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    orch = PaymentOrchestrator()

    entry = orch.charge(order_id=44, amount=20000)

    print("CHARGE:", entry)

    orch.retry_failed(entry.id)

    dispute = orch.raise_dispute(44, "customer complaint")

    print("DISPUTE:", dispute)

    print("CSV EXPORT")
    print(orch.export_ledger_csv())