"""
=====================================================
FLIPTRYBE SEGMENT 52
AD AUCTION & BID RANKING ENGINE
=====================================================
Runs:
second-price auctions,
geo weighting,
category multipliers,
quality score ranking,
fair clearing prices.
=====================================================
"""

from dataclasses import dataclass, field
from typing import List, Dict

from app.segments.segment_49_ads_engine import ACTIVE_CAMPAIGNS
from app.segments.segment_50_ads_billing import charge_wallet
from app.segments.segment_51_ads_analytics import aggregate_campaign_metrics


# =====================================================
# QUALITY SCORE MODEL
# =====================================================

@dataclass
class QualityScore:

    ctr: float
    roi: float
    freshness: float

    @property
    def score(self):

        return (
            (self.ctr * 0.5)
            + (self.roi * 0.3)
            + (self.freshness * 0.2)
        )


# =====================================================
# AUCTION ENTRY
# =====================================================

@dataclass
class AuctionEntry:

    campaign_id: int
    bid: float
    quality: float
    final_score: float = 0.0


# =====================================================
# HELPERS
# =====================================================

def geo_multiplier(campaign, geo):

    return 1.2 if geo in campaign.geo_targets else 0.7


def category_multiplier(campaign, category):

    return 1.1 if category in campaign.categories else 0.8


def freshness_factor(campaign):

    return max(0.3, 1.0 - (campaign.age_days * 0.02))


# =====================================================
# RUN AUCTION
# =====================================================

def run_auction(geo: str, category: str):

    metrics = aggregate_campaign_metrics()

    pool: List[AuctionEntry] = []

    for camp in ACTIVE_CAMPAIGNS.values():

        if camp.daily_budget <= 0:
            continue

        bid = camp.max_cpc
        bid *= geo_multiplier(camp, geo)
        bid *= category_multiplier(camp, category)

        m = metrics.get(camp.campaign_id)

        quality = 0.5

        if m:
            q = QualityScore(
                ctr=m.ctr,
                roi=m.roi,
                freshness=freshness_factor(camp),
            )
            quality = q.score

        pool.append(
            AuctionEntry(
                campaign_id=camp.campaign_id,
                bid=bid,
                quality=quality,
            )
        )

    if not pool:
        return None

    for p in pool:
        p.final_score = p.bid * p.quality

    pool.sort(key=lambda x: x.final_score, reverse=True)

    winner = pool[0]
    clearing_price = pool[1].bid if len(pool) > 1 else winner.bid * 0.8

    return {
        "winner_campaign_id": winner.campaign_id,
        "price": round(clearing_price, 2),
        "ranking": pool,
    }


# =====================================================
# CHARGE AFTER WIN
# =====================================================

def execute_auction(geo: str, category: str):

    result = run_auction(geo, category)

    if not result:
        return None

    cid = result["winner_campaign_id"]
    price = result["price"]

    charge_wallet(cid, price)

    return result


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    from app.segments.segment_49_ads_engine import AdCampaign, register_campaign
    from app.segments.segment_50_ads_billing import fund_wallet

    fund_wallet(7, 15000)

    c1 = AdCampaign(
        campaign_id=31,
        merchant_id=7,
        listing_id=401,
        max_cpc=300,
        daily_budget=8000,
        geo_targets=["lagos"],
        categories=["phones"],
    )

    c2 = AdCampaign(
        campaign_id=32,
        merchant_id=7,
        listing_id=402,
        max_cpc=250,
        daily_budget=8000,
        geo_targets=["lagos"],
        categories=["phones"],
    )

    register_campaign(c1)
    register_campaign(c2)

    print(execute_auction("lagos", "phones"))