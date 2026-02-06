"""
=====================================================
FLIPTRYBE SEGMENT 74
BILLING & FINANCE ENGINE
=====================================================
Responsibilities:
1. Subscription plans
2. Invoice generation
3. Tax calculation
4. VAT/GST rules
5. Proration
6. Refund processing
7. Receipts
8. Revenue recognition
9. Finance exports
10. Account balances
=====================================================
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List
import uuid
import csv
import io


# =====================================================
# MODELS
# =====================================================

@dataclass
class Plan:
    id: str
    name: str
    monthly_price: float


@dataclass
class Subscription:
    id: str
    user_id: int
    plan_id: str
    started_at: datetime
    active: bool = True


@dataclass
class Invoice:
    id: str
    user_id: int
    amount: float
    tax: float
    total: float
    issued_at: datetime = field(default_factory=datetime.utcnow)
    paid: bool = False


@dataclass
class Receipt:
    id: str
    invoice_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)


# =====================================================
# STORES
# =====================================================

PLANS: Dict[str, Plan] = {}
SUBSCRIPTIONS: Dict[str, Subscription] = {}
INVOICES: Dict[str, Invoice] = {}
RECEIPTS: Dict[str, Receipt] = {}


# =====================================================
# PLANS
# =====================================================

def create_plan(name: str, monthly_price: float):

    pid = str(uuid.uuid4())

    PLANS[pid] = Plan(pid, name, monthly_price)
    return PLANS[pid]


# =====================================================
# SUBSCRIPTIONS
# =====================================================

def subscribe(user_id: int, plan_id: str):

    sid = str(uuid.uuid4())

    SUBSCRIPTIONS[sid] = Subscription(
        id=sid,
        user_id=user_id,
        plan_id=plan_id,
        started_at=datetime.utcnow(),
    )

    return SUBSCRIPTIONS[sid]


# =====================================================
# TAX ENGINE
# =====================================================

TAX_RULES = {
    "NG": 0.075,
    "EU": 0.20,
}


def compute_tax(country: str, amount: float):

    rate = TAX_RULES.get(country, 0)

    return round(amount * rate, 2)


# =====================================================
# PRORATION
# =====================================================

def prorate(sub: Subscription):

    days = (datetime.utcnow() - sub.started_at).days

    return round(days / 30, 2)


# =====================================================
# INVOICES
# =====================================================

def generate_invoice(user_id: int, amount: float, country="NG"):

    tax = compute_tax(country, amount)

    inv = Invoice(
        id=str(uuid.uuid4()),
        user_id=user_id,
        amount=amount,
        tax=tax,
        total=amount + tax,
    )

    INVOICES[inv.id] = inv
    return inv


# =====================================================
# PAY INVOICE
# =====================================================

def pay_invoice(invoice_id: str):

    inv = INVOICES[invoice_id]
    inv.paid = True

    r = Receipt(
        id=str(uuid.uuid4()),
        invoice_id=invoice_id,
    )

    RECEIPTS[r.id] = r
    return r


# =====================================================
# REFUNDS
# =====================================================

def refund(invoice_id: str):

    inv = INVOICES[invoice_id]

    inv.paid = False
    return inv


# =====================================================
# REVENUE RECOGNITION
# =====================================================

def recognize_revenue(start: datetime, end: datetime):

    rev = 0

    for i in INVOICES.values():
        if start <= i.issued_at <= end and i.paid:
            rev += i.total

    return rev


# =====================================================
# EXPORT
# =====================================================

def export_finance_csv():

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["invoice_id", "user_id", "total", "paid"])

    for i in INVOICES.values():
        writer.writerow([
            i.id,
            i.user_id,
            i.total,
            i.paid,
        ])

    return output.getvalue()


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    p = create_plan("Pro Seller", 5000)

    s = subscribe(3, p.id)

    inv = generate_invoice(3, p.monthly_price)

    print("INVOICE:", inv)

    rec = pay_invoice(inv.id)

    print("RECEIPT:", rec)

    print("REVENUE:", recognize_revenue(datetime.utcnow() - timedelta(days=1), datetime.utcnow()))