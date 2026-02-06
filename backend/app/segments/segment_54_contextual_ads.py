"""
=====================================================
FLIPTRYBE SEGMENT 54
CONTEXTUAL AD RELEVANCE ENGINE
=====================================================
Selects best creative variant per impression using:
semantic intent,
creative fatigue,
fairness balancing,
category inference.
=====================================================
"""

import math
import random
from collections import defaultdict
from typing import Dict, List

from app.segments.segment_49_ads_engine import AdCampaign
from app.segments.segment_52_ad_auction import run_auction


# =====================================================
# CREATIVE STORE
# =====================================================

CREATIVES: Dict[int, List[Dict]] = defaultdict(list)
CREATIVE_IMPRESSIONS: Dict[str, int] = defaultdict(int)


# =====================================================
# REGISTER CREATIVE
# =====================================================

def register_creative(
    *,
    campaign_id: int,
    creative_id: str,
    headline: str,
    image_url: str,
    category: str,
):

    CREATIVES[campaign_id].append(
        {
            "creative_id": creative_id,
            "headline": headline,
            "image_url": image_url,
            "category": category,
        }
    )


# =====================================================
# INTENT INFERENCE (LIGHTWEIGHT)
# =====================================================

KEYWORDS = {
    "phone": "electronics",
    "laptop": "electronics",
    "rent": "shortlet",
    "apartment": "shortlet",
    "bike": "transport",
}


def infer_category(query: str):

    q = query.lower()

    for k, v in KEYWORDS.items():
        if k in q:
            return v

    return "general"


# =====================================================
# FATIGUE CONTROL
# =====================================================

def fatigue_penalty(creative_id: str):

    views = CREATIVE_IMPRESSIONS[creative_id]

    if views < 20:
        return 1.0

    return max(0.3, 1 - views / 200)


# =====================================================
# FAIRNESS BALANCER
# =====================================================

def fairness_boost(campaign_id: int):

    return random.uniform(0.95, 1.05)


# =====================================================
# SELECT CREATIVE
# =====================================================

def select_creative(
    *,
    user_query: str,
    geo: str,
):

    category = infer_category(user_query)

    auction = run_auction(geo, category)

    if not auction:
        return None

    winner_id = auction["winner_campaign_id"]

    creatives = CREATIVES.get(winner_id)

    if not creatives:
        return None

    scored = []

    for c in creatives:

        fatigue = fatigue_penalty(c["creative_id"])
        fairness = fairness_boost(winner_id)

        score = fatigue * fairness

        scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)

    best = scored[0][1]

    CREATIVE_IMPRESSIONS[best["creative_id"]] += 1

    return {
        "campaign_id": winner_id,
        "creative": best,
        "category": category,
    }


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    from app.segments.segment_49_ads_engine import AdCampaign, register_campaign

    camp = AdCampaign(
        campaign_id=55,
        merchant_id=12,
        listing_id=301,
        max_cpc=250,
        daily_budget=5000,
        geo_targets=["lagos"],
        categories=["electronics"],
    )

    register_campaign(camp)

    register_creative(
        campaign_id=55,
        creative_id="c1",
        headline="Hot iPhones in Ikeja",
        image_url="/img/iphone.png",
        category="electronics",
    )

    print(select_creative(user_query="cheap iphone", geo="lagos"))