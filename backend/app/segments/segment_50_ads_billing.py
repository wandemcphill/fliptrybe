"""
=====================================================
FLIPTRYBE SEGMENT 50
ADS BILLING & LEDGER SYSTEM
=====================================================
Handles:
wallet funding, CPC debits,
invoice generation,
reconciliation and fraud locks.
=====================================================
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List

from app.segments.segment_49_ads_engine import record_click, AdCampaign


# =====================================================
# MERCHANT AD WALLET
# =====================================================

@dataclass
class AdWallet:

    merchant_id: int
    balance: float = 0.0
    locked: bool = False
    updated_ts: float = field(default_factory=time.time)


# =====================================================
# INVOICE MODEL
# =====================================================

@dataclass
class Invoice:

    invoice_id: str
    merchant_id: int
    amount: float
    line_items: List[Dict]
    status: str = "open"
    created_ts: float = field(default_factory=time.time)


# =====================================================
# REGISTRY
# =====================================================

WALLETS: Dict[int, AdWallet] = {}
INVOICES: Dict[str, Invoice] = {}


# =====================================================
# WALLET OPS
# =====================================================

def get_wallet(merchant_id: int):

    if merchant_id not in WALLETS:
        WALLETS[merchant_id] = AdWallet(merchant_id=merchant_id)

    return WALLETS[merchant_id]


def fund_wallet(merchant_id: int, amount: float):

    wallet = get_wallet(merchant_id)

    if wallet.locked:
        raise RuntimeError("Wallet locked for review")

    wallet.balance += amount
    wallet.updated_ts = time.time()

    return wallet.balance


# =====================================================
# CPC DEBIT
# =====================================================

def debit_for_click(
    *,
    campaign: AdCampaign,
    cpc: float,
):

    wallet = get_wallet(campaign.merchant_id)

    if wallet.locked:
        raise RuntimeError("Wallet frozen")

    if wallet.balance < cpc:
        raise RuntimeError("Insufficient ad balance")

    wallet.balance -= cpc

    record_click(
        campaign=campaign,
        cpc_paid=cpc,
    )

    invoice = Invoice(
        invoice_id=str(uuid.uuid4()),
        merchant_id=campaign.merchant_id,
        amount=cpc,
        line_items=[
            {
                "campaign_id": campaign.campaign_id,
                "listing_id": campaign.listing_id,
                "type": "click",
                "cpc": cpc,
                "ts": time.time(),
            }
        ],
    )

    INVOICES[invoice.invoice_id] = invoice

    return invoice


# =====================================================
# DAILY STATEMENT
# =====================================================

def daily_statement(merchant_id: int):

    return [
        inv
        for inv in INVOICES.values()
        if inv.merchant_id == merchant_id
    ]


# =====================================================
# FRAUD LOCK
# =====================================================

def lock_wallet(merchant_id: int):

    wallet = get_wallet(merchant_id)
    wallet.locked = True


def unlock_wallet(merchant_id: int):

    wallet = get_wallet(merchant_id)
    wallet.locked = False


# =====================================================
# RECONCILIATION JOB
# =====================================================

def reconcile_campaign_spend(
    campaigns: List[AdCampaign],
):

    mismatches = []

    for c in campaigns:

        wallet = get_wallet(c.merchant_id)

        if c.spent_today > wallet.balance + 1000:
            mismatches.append(
                (c.campaign_id, c.spent_today, wallet.balance)
            )

    return mismatches


# =====================================================
# PAYSTACK BRIDGE (STUB)
# =====================================================

def initiate_paystack_funding(
    merchant_id: int,
    amount: float,
):

    ref = f"AD-{uuid.uuid4()}"

    return {
        "reference": ref,
        "amount": amount,
        "provider": "paystack",
    }


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    wallet = fund_wallet(7, 50000)

    print("Wallet:", wallet)

    camp = AdCampaign(
        campaign_id=1,
        merchant_id=7,
        listing_id=9,
        max_cpc=200,
        daily_budget=5000,
        geo_targets=["lagos"],
        categories=["phones"],
    )

    inv = debit_for_click(
        campaign=camp,
        cpc=150,
    )

    print("Invoice:", inv)