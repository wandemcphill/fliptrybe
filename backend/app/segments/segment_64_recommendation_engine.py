"""
=====================================================
FLIPTRYBE SEGMENT 64
RECOMMENDATION ENGINE CORE
=====================================================
Feed ranking with:
- Bayesian preference modeling
- Signal weighting
- Time decay curves
- Trending amplification
=====================================================
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime, timedelta


# =====================================================
# SIGNAL TYPES
# =====================================================

SIGNAL_WEIGHTS = {
    "view": 1.0,
    "save": 3.0,
    "message": 4.0,
    "purchase": 6.0,
    "share": 5.0,
}


# =====================================================
# MODELS
# =====================================================

@dataclass
class FeedSignal:
    user_id: int
    listing_id: int
    signal_type: str
    weight: float
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ListingScore:
    listing_id: int
    base_score: float = 0.0
    trending_score: float = 0.0
    final_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserProfile:
    user_id: int
    category_affinity: Dict[str, float] = field(default_factory=dict)
    state_affinity: Dict[str, float] = field(default_factory=dict)


# =====================================================
# STORES (IN MEMORY)
# =====================================================

SIGNALS: List[FeedSignal] = []
LISTING_SCORES: Dict[int, ListingScore] = {}
USER_PROFILES: Dict[int, UserProfile] = {}


# =====================================================
# INGESTION
# =====================================================

def ingest_signal(user_id: int, listing_id: int, signal_type: str):

    weight = SIGNAL_WEIGHTS.get(signal_type, 1.0)

    sig = FeedSignal(
        user_id=user_id,
        listing_id=listing_id,
        signal_type=signal_type,
        weight=weight
    )

    SIGNALS.append(sig)


# =====================================================
# TIME DECAY
# =====================================================

def decay_weight(signal: FeedSignal):

    age_hours = (datetime.utcnow() - signal.created_at).total_seconds() / 3600
    half_life = 24

    return signal.weight * math.exp(-age_hours / half_life)


# =====================================================
# USER MODEL UPDATE
# =====================================================

def update_user_profile(user_id: int, category: str, state: str, delta: float):

    profile = USER_PROFILES.setdefault(user_id, UserProfile(user_id))

    profile.category_affinity[category] = (
        profile.category_affinity.get(category, 0.0) + delta
    )

    profile.state_affinity[state] = (
        profile.state_affinity.get(state, 0.0) + delta
    )


# =====================================================
# LISTING SCORING
# =====================================================

def compute_listing_score(listing_id: int):

    score = 0.0

    for sig in SIGNALS:
        if sig.listing_id == listing_id:
            score += decay_weight(sig)

    trending = compute_trending_boost(listing_id)

    final = score + trending

    listing_score = LISTING_SCORES.setdefault(
        listing_id,
        ListingScore(listing_id)
    )

    listing_score.base_score = score
    listing_score.trending_score = trending
    listing_score.final_score = final
    listing_score.last_updated = datetime.utcnow()

    return listing_score


# =====================================================
# TRENDING BOOST
# =====================================================

def compute_trending_boost(listing_id: int):

    recent_cutoff = datetime.utcnow() - timedelta(hours=6)

    recent = [
        sig for sig in SIGNALS
        if sig.listing_id == listing_id and sig.created_at >= recent_cutoff
    ]

    return sum(sig.weight for sig in recent) * 0.3


# =====================================================
# PERSONALIZED RANKING
# =====================================================

def rank_feed_for_user(
    user_id: int,
    listings: List[Dict],
):

    profile = USER_PROFILES.get(user_id)

    ranked = []

    for listing in listings:

        lid = listing["id"]
        category = listing.get("category")
        state = listing.get("state")

        score_obj = compute_listing_score(lid)

        affinity = 0.0

        if profile:
            affinity += profile.category_affinity.get(category, 0.0)
            affinity += profile.state_affinity.get(state, 0.0)

        cold_start_boost = 5.0 if score_obj.base_score < 3 else 0

        final_score = score_obj.final_score + affinity + cold_start_boost

        ranked.append((final_score, listing))

    ranked.sort(reverse=True, key=lambda x: x[0])

    return [l for _, l in ranked]


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    ingest_signal(1, 101, "view")
    ingest_signal(1, 101, "save")
    ingest_signal(2, 101, "purchase")

    ingest_signal(3, 102, "view")

    update_user_profile(1, "electronics", "lagos", 2)

    listings = [
        {"id": 101, "category": "electronics", "state": "lagos"},
        {"id": 102, "category": "furniture", "state": "abuja"},
    ]

    ranked = rank_feed_for_user(1, listings)

    for l in ranked:
        print(l["id"])