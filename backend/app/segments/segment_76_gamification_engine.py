"""
=====================================================
FLIPTRYBE SEGMENT 76
GAMIFICATION & ENGAGEMENT CORE
=====================================================
Responsibilities:
1. Badge system
2. Leaderboards
3. Quest engine
4. Reward wallets
5. Streak tracking
6. Event hooks
7. Prize pools
8. Anti-cheat
9. Metrics
10. Seasonal resets
=====================================================
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List
import uuid


# =====================================================
# MODELS
# =====================================================

@dataclass
class Badge:
    id: str
    name: str
    description: str


@dataclass
class Quest:
    id: str
    name: str
    goal: int
    reward: int


@dataclass
class Wallet:
    user_id: int
    points: int = 0


@dataclass
class Streak:
    user_id: int
    days: int = 0
    last_active: datetime = field(default_factory=datetime.utcnow)


# =====================================================
# STORES
# =====================================================

BADGES: Dict[str, Badge] = {}
QUESTS: Dict[str, Quest] = {}
WALLETS: Dict[int, Wallet] = {}
STREAKS: Dict[int, Streak] = {}
LEADERBOARD: Dict[int, int] = {}


# =====================================================
# BADGES
# =====================================================

def create_badge(name, desc):

    b = Badge(str(uuid.uuid4()), name, desc)
    BADGES[b.id] = b
    return b


# =====================================================
# QUESTS
# =====================================================

def create_quest(name, goal, reward):

    q = Quest(str(uuid.uuid4()), name, goal, reward)
    QUESTS[q.id] = q
    return q


# =====================================================
# WALLET
# =====================================================

def get_wallet(user_id):

    return WALLETS.setdefault(user_id, Wallet(user_id))


# =====================================================
# STREAK
# =====================================================

def update_streak(user_id):

    s = STREAKS.setdefault(user_id, Streak(user_id))

    if datetime.utcnow() - s.last_active <= timedelta(days=1):
        s.days += 1
    else:
        s.days = 1

    s.last_active = datetime.utcnow()
    return s


# =====================================================
# EVENTS
# =====================================================

def record_event(user_id, event_type):

    wallet = get_wallet(user_id)

    wallet.points += 1
    LEADERBOARD[user_id] = wallet.points

    update_streak(user_id)


# =====================================================
# PRIZE POOLS
# =====================================================

PRIZE_POOLS: Dict[str, int] = {}


def fund_prize_pool(season: str, amount: int):

    PRIZE_POOLS[season] = PRIZE_POOLS.get(season, 0) + amount


# =====================================================
# ANTI CHEAT
# =====================================================

def detect_cheat(user_id):

    s = STREAKS.get(user_id)

    if s and s.days > 365:
        return True

    return False


# =====================================================
# METRICS
# =====================================================

def engagement_snapshot():

    return {
        "users": len(WALLETS),
        "points_total": sum(w.points for w in WALLETS.values()),
        "active_streaks": len([s for s in STREAKS.values() if s.days > 0]),
    }


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    create_badge("Starter", "Joined FlipTrybe")

    q = create_quest("List 5 items", 5, 50)

    record_event(1, "login")
    record_event(1, "post")

    fund_prize_pool("2026Q1", 10000)

    print("ENGAGEMENT:", engagement_snapshot())