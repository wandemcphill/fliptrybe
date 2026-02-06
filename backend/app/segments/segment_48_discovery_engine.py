"""
=====================================================
FLIPTRYBE SEGMENT 48
AI DISCOVERY & SEARCH RANKING ENGINE
=====================================================
Generates personalized listing rankings using:
price, proximity, merchant momentum, trust score,
user intent, and recent activity.
=====================================================
"""

import math
import time
from typing import List, Dict, Optional

from app.segments.segment_47_merchant_performance import merchant_snapshot
from app.segments.segment_46_user_interest_graph import get_user_interest_profile
from app.segments.segment_45_geo_engine import geo_distance_km
from app.segments.segment_33_trust_engine import user_trust_score


# =====================================================
# WEIGHT CONSTANTS
# =====================================================

WEIGHTS = {
    "text_match": 0.25,
    "price_value": 0.15,
    "distance": 0.15,
    "merchant_momentum": 0.15,
    "trust": 0.15,
    "recency": 0.10,
    "intent": 0.05,
}


# =====================================================
# TEXT MATCHING
# =====================================================

def fuzzy_match_score(query: str, text: str):

    q = query.lower()
    t = text.lower()

    hits = sum(1 for w in q.split() if w in t)

    return hits / max(1, len(q.split()))


# =====================================================
# PRICE VALUE SIGNAL
# =====================================================

def price_score(price: float, market_avg: float):

    if price <= market_avg:
        return 1.0

    delta = price - market_avg
    return max(0.0, 1 - delta / market_avg)


# =====================================================
# RECENCY BOOST
# =====================================================

def recency_score(created_ts: float):

    hours = (time.time() - created_ts) / 3600

    if hours < 6:
        return 1.0

    if hours < 48:
        return 0.7

    if hours < 168:
        return 0.4

    return 0.1


# =====================================================
# DISCOVERY SCORE
# =====================================================

def discovery_score(
    *,
    user_id: int,
    listing: Dict,
    market_avg: float,
    user_lat: float,
    user_lng: float,
):

    text = fuzzy_match_score(
        listing.get("title", "") + " " + listing.get("description", ""),
        listing.get("query", ""),
    )

    price = price_score(listing["price"], market_avg)

    distance_km = geo_distance_km(
        user_lat,
        user_lng,
        listing["lat"],
        listing["lng"],
    )

    distance = 1 / (1 + distance_km)

    merchant = merchant_snapshot(listing["seller_id"])
    momentum = min(1.0, merchant["weekly_sales"] / 2_000_000)

    trust = user_trust_score(listing["seller_id"]) / 100

    recency = recency_score(listing["created_ts"])

    interest = get_user_interest_profile(user_id).get(
        listing.get("category"), 0.2
    )

    final_score = (
        WEIGHTS["text_match"] * text +
        WEIGHTS["price_value"] * price +
        WEIGHTS["distance"] * distance +
        WEIGHTS["merchant_momentum"] * momentum +
        WEIGHTS["trust"] * trust +
        WEIGHTS["recency"] * recency +
        WEIGHTS["intent"] * interest
    )

    return round(final_score, 4)


# =====================================================
# RANKER
# =====================================================

def rank_listings(
    *,
    user_id: int,
    listings: List[Dict],
    query: str,
    user_lat: float,
    user_lng: float,
):

    if not listings:
        return []

    avg_price = sum(l["price"] for l in listings) / len(listings)

    for l in listings:
        l["query"] = query
        l["score"] = discovery_score(
            user_id=user_id,
            listing=l,
            market_avg=avg_price,
            user_lat=user_lat,
            user_lng=user_lng,
        )

    return sorted(listings, key=lambda x: x["score"], reverse=True)


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    listings = [
        {
            "id": 1,
            "title": "iPhone 13 Pro",
            "description": "Clean unlocked device",
            "price": 550000,
            "seller_id": 7,
            "lat": 6.5,
            "lng": 3.3,
            "created_ts": time.time() - 7200,
            "category": "phones",
        },
        {
            "id": 2,
            "title": "Samsung Galaxy S21",
            "description": "Slightly used",
            "price": 480000,
            "seller_id": 11,
            "lat": 6.6,
            "lng": 3.5,
            "created_ts": time.time() - 90000,
            "category": "phones",
        },
    ]

    ranked = rank_listings(
        user_id=99,
        listings=listings,
        query="iphone phone",
        user_lat=6.52,
        user_lng=3.38,
    )

    for r in ranked:
        print(r["id"], r["score"])