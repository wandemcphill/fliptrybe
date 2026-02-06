"""
=====================================================
FLIPTRYBE SEGMENT 65
ADS AUCTION & SPONSORED RANKING ENGINE
=====================================================
Handles:
- CPC / CPM bidding
- Second price auctions
- Budget enforcement
- Impression tracking
- Sponsored feed boosting
- Fairness dampening
- Billing hooks
=====================================================
"""

from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime
import random


# =====================================================
# MODELS
# =====================================================

@dataclass
class AdCampaign:
    id: int
    merchant_id: int
    listing_id: int
    bid_amount: float
    daily_budget: float
    spent_today: float = 0.0
    is_active: bool = True


@dataclass
class Impression:
    campaign_id: int
    user_id: int
    cost: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AuctionResult:
    campaign: AdCampaign
    clearing_price: float


# =====================================================
# STORES (IN MEMORY)
# =====================================================

CAMPAIGNS: Dict[int, AdCampaign] = {}
IMPRESSIONS: List[Impression] = []


# =====================================================
# CAMPAIGN MGMT
# =====================================================

def register_campaign(
    merchant_id: int,
    listing_id: int,
    bid_amount: float,
    daily_budget: float,
):

    cid = len(CAMPAIGNS) + 1

    CAMPAIGNS[cid] = AdCampaign(
        id=cid,
        merchant_id=merchant_id,
        listing_id=listing_id,
        bid_amount=bid_amount,
        daily_budget=daily_budget,
    )

    return CAMPAIGNS[cid]


# =====================================================
# FAIRNESS CONTROL
# =====================================================

def fairness_multiplier(campaign: AdCampaign):

    # Prevent whales from dominating
    saturation = campaign.spent_today / max(campaign.daily_budget, 1)

    if saturation > 0.8:
        return 0.6
    if saturation > 0.5:
        return 0.8
    return 1.0


# =====================================================
# AUCTION LOGIC (SECOND PRICE)
# =====================================================

def run_auction(user_id: int, eligible_listing_ids: List[int]):

    candidates = [
        c for c in CAMPAIGNS.values()
        if c.is_active
        and c.listing_id in eligible_listing_ids
        and c.spent_today < c.daily_budget
    ]

    if not candidates:
        return None

    scored = []

    for c in candidates:
        effective_bid = c.bid_amount * fairness_multiplier(c)
        scored.append((effective_bid, c))

    scored.sort(reverse=True, key=lambda x: x[0])

    winner_bid, winner = scored[0]

    second_price = scored[1][0] if len(scored) > 1 else winner_bid * 0.7

    return AuctionResult(
        campaign=winner,
        clearing_price=round(second_price, 2),
    )


# =====================================================
# BILLING
# =====================================================

def bill_impression(result: AuctionResult, user_id: int):

    result.campaign.spent_today += result.clearing_price

    IMPRESSIONS.append(
        Impression(
            campaign_id=result.campaign.id,
            user_id=user_id,
            cost=result.clearing_price,
        )
    )


# =====================================================
# FEED INJECTION
# =====================================================

def inject_sponsored(listings: List[Dict], user_id: int):

    ids = [l["id"] for l in listings]

    result = run_auction(user_id, ids)

    if not result:
        return listings

    bill_impression(result, user_id)

    for i, l in enumerate(listings):
        if l["id"] == result.campaign.listing_id:
            boosted = listings.pop(i)
            listings.insert(0, boosted)
            boosted["sponsored"] = True
            boosted["ad_cost"] = result.clearing_price
            break

    return listings


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    register_campaign(10, 201, 4.5, 100)
    register_campaign(11, 202, 6.0, 40)

    feed = [
        {"id": 201},
        {"id": 202},
        {"id": 203},
    ]

    final_feed = inject_sponsored(feed, user_id=99)

    for item in final_feed:
        print(item)