"""
=====================================================
FLIPTRYBE SEGMENT 56
ADS ADMIN CONTROL PLANE
=====================================================
Allows:
campaign suspension,
wallet freezing,
forced refunds,
audit tagging,
override logging.
=====================================================
"""

import time
from typing import Dict

from app.segments.segment_49_ads_engine import ACTIVE_CAMPAIGNS
from app.segments.segment_50_ads_billing import (
    WALLETS,
    INVOICES,
    lock_wallet,
    unlock_wallet,
)
from app.segments.segment_52_ad_auction import run_auction


# =====================================================
# ADMIN AUDIT LOG
# =====================================================

AUDIT_LOG = []


def audit(action: str, payload: Dict):

    AUDIT_LOG.append(
        {
            "ts": time.time(),
            "action": action,
            "payload": payload,
        }
    )


# =====================================================
# CAMPAIGN CONTROLS
# =====================================================

def suspend_campaign(campaign_id: int):

    camp = ACTIVE_CAMPAIGNS.get(campaign_id)

    if not camp:
        raise KeyError("Campaign not found")

    camp.suspended = True

    audit("suspend_campaign", {"campaign_id": campaign_id})


def resume_campaign(campaign_id: int):

    camp = ACTIVE_CAMPAIGNS.get(campaign_id)

    if not camp:
        raise KeyError("Campaign not found")

    camp.suspended = False

    audit("resume_campaign", {"campaign_id": campaign_id})


# =====================================================
# WALLET CONTROLS
# =====================================================

def freeze_wallet(merchant_id: int):

    lock_wallet(merchant_id)

    audit("freeze_wallet", {"merchant_id": merchant_id})


def unfreeze_wallet(merchant_id: int):

    unlock_wallet(merchant_id)

    audit("unfreeze_wallet", {"merchant_id": merchant_id})


# =====================================================
# FORCE REFUND
# =====================================================

def force_refund(invoice_id: str):

    inv = INVOICES.get(invoice_id)

    if not inv:
        raise KeyError("Invoice not found")

    wallet = WALLETS.get(inv.merchant_id)

    if wallet:
        wallet.balance += inv.amount

    inv.status = "refunded"

    audit(
        "force_refund",
        {
            "invoice_id": invoice_id,
            "merchant_id": inv.merchant_id,
        },
    )


# =====================================================
# OVERRIDE AUCTION
# =====================================================

def override_auction(geo: str, category: str, forced_campaign_id: int):

    audit(
        "override_auction",
        {
            "geo": geo,
            "category": category,
            "forced_campaign_id": forced_campaign_id,
        },
    )

    return {
        "forced_campaign_id": forced_campaign_id,
        "geo": geo,
        "category": category,
    }


# =====================================================
# VIEW AUDIT LOG
# =====================================================

def admin_activity():

    return AUDIT_LOG[-200:]


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    print("🛠 Admin console online")

    freeze_wallet(7)

    print("Audit:", admin_activity())