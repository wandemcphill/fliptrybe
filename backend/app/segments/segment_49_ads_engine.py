"""
=====================================================
FLIPTRYBE SEGMENT 49
PROMOTED LISTINGS & CPC AUCTION ENGINE
=====================================================
Handles paid exposure with:
auction ranking, pacing, targeting,
click tracking, fraud signals.
=====================================================
"""

import time
import random
from typing import Dict, List

from app.segments.segment_48_discovery_engine import discovery_score
from app.segments.segment_33_trust_engine import user_trust_score


# =====================================================
# CAMPAIGN MODEL
# =====================================================

class AdCampaign:

    def __init__(
        self,
        *,
        campaign_id: int,
        merchant_id: int,
        listing_id: int,
        max_cpc: float,
        daily_budget: float,
        geo_targets: List[str],
        categories: List[str],
    ):

        self.campaign_id = campaign_id
        self.merchant_id = merchant_id
        self.listing_id = listing_id

        self.max_cpc = max_cpc
        self.daily_budget = daily_budget

        self.geo_targets = geo_targets
        self.categories = categories

        self.spent_today = 0.0
        self.last_reset = time.time()


# =====================================================
# FRAUD HEURISTICS
# =====================================================

def suspicious_click_rate(clicks: int, impressions: int):

    if impressions < 10:
        return False

    ctr = clicks / impressions

    return ctr > 0.5


# =====================================================
# PACING
# =====================================================

def pace_budget(campaign: AdCampaign):

    if time.time() - campaign.last_reset > 86400:
        campaign.spent_today = 0
        campaign.last_reset = time.time()

    return campaign.spent_today < campaign.daily_budget


# =====================================================
# AUCTION SCORING
# =====================================================

def ad_rank_score(
    *,
    campaign: AdCampaign,
    base_relevance: float,
    user_id: int,
):

    trust = user_trust_score(campaign.merchant_id) / 100

    quality = base_relevance * trust

    return campaign.max_cpc * quality


# =====================================================
# PROMOTED SELECTION
# =====================================================

def select_promoted(
    *,
    user_id: int,
    listings: List[Dict],
    campaigns: List[AdCampaign],
    user_geo: str,
    category: str,
):

    eligible = []

    for c in campaigns:

        if not pace_budget(c):
            continue

        if category not in c.categories:
            continue

        if user_geo not in c.geo_targets:
            continue

        listing = next(
            (l for l in listings if l["id"] == c.listing_id),
            None,
        )

        if not listing:
            continue

        relevance = discovery_score(
            user_id=user_id,
            listing=listing,
            market_avg=listing["price"],
            user_lat=listing["lat"],
            user_lng=listing["lng"],
        )

        score = ad_rank_score(
            campaign=c,
            base_relevance=relevance,
            user_id=user_id,
        )

        eligible.append((score, c, listing))

    eligible.sort(key=lambda x: x[0], reverse=True)

    return eligible


# =====================================================
# CLICK EVENT
# =====================================================

def record_click(
    *,
    campaign: AdCampaign,
    cpc_paid: float,
):

    campaign.spent_today += cpc_paid


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    campaigns = [
        AdCampaign(
            campaign_id=1,
            merchant_id=7,
            listing_id=1,
            max_cpc=200,
            daily_budget=10000,
            geo_targets=["lagos"],
            categories=["phones"],
        )
    ]

    listings = [
        {
            "id": 1,
            "title": "iPhone 13 Pro",
            "description": "Clean unlocked",
            "price": 550000,
            "seller_id": 7,
            "lat": 6.5,
            "lng": 3.3,
            "created_ts": time.time(),
            "category": "phones",
        }
    ]

    winners = select_promoted(
        user_id=3,
        listings=listings,
        campaigns=campaigns,
        user_geo="lagos",
        category="phones",
    )

    for score, campaign, listing in winners:
        print("PROMOTED:", listing["id"], score)