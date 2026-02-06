"""
=====================================================
FLIPTRYBE SEGMENT 47
MERCHANT PERFORMANCE & INCENTIVE ENGINE
=====================================================
Tracks merchant sales, builds leaderboards,
adjusts commission tiers, and celebrates top sellers.
=====================================================
"""

import json
import time
from pathlib import Path
from typing import Dict, List

from app.segments.segment_44_compliance_engine import append_ledger


ROOT = Path.cwd()
DATA_FILE = ROOT / "merchant_stats.json"


# =====================================================
# STORAGE
# =====================================================

def load_stats():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return {}


def save_stats(stats):
    DATA_FILE.write_text(json.dumps(stats, indent=2))


# =====================================================
# SALES INGEST
# =====================================================

def record_sale(merchant_id: int, amount: float, delivery_used: bool):

    stats = load_stats()

    m = stats.setdefault(
        str(merchant_id),
        {
            "total_sales": 0.0,
            "weekly_sales": [],
            "delivery_sales": 0.0,
            "orders": 0,
            "region": None,
        },
    )

    m["total_sales"] += amount
    m["weekly_sales"].append({"amount": amount, "ts": time.time()})
    m["orders"] += 1

    if delivery_used:
        m["delivery_sales"] += amount

    save_stats(stats)

    append_ledger(
        "merchant_sale",
        {
            "merchant_id": merchant_id,
            "amount": amount,
            "delivery_used": delivery_used,
        },
    )


# =====================================================
# LEADERBOARDS
# =====================================================

def leaderboard(region: str = None, limit=10):

    stats = load_stats()

    records = []

    for mid, data in stats.items():

        if region and data.get("region") != region:
            continue

        records.append(
            {
                "merchant_id": mid,
                "total_sales": data["total_sales"],
                "orders": data["orders"],
            }
        )

    records.sort(key=lambda x: x["total_sales"], reverse=True)

    return records[:limit]


def weekly_leaderboard(limit=10):

    now = time.time()
    stats = load_stats()
    records = []

    for mid, data in stats.items():

        week_sales = sum(
            s["amount"]
            for s in data["weekly_sales"]
            if s["ts"] > now - 7 * 86400
        )

        records.append(
            {
                "merchant_id": mid,
                "weekly_sales": week_sales,
            }
        )

    records.sort(key=lambda x: x["weekly_sales"], reverse=True)

    return records[:limit]


# =====================================================
# COMMISSION TIERS
# =====================================================

def commission_rate(merchant_id: int):

    stats = load_stats()
    m = stats.get(str(merchant_id))

    if not m:
        return 0.15  # default platform take

    if m["total_sales"] >= 15_000_000:
        return 0.03  # elite tier

    return 0.15


def delivery_bonus(merchant_id: int):

    rate = commission_rate(merchant_id)

    if rate == 0.03:
        return 0.05

    return 0.0


# =====================================================
# SNAPSHOT FOR DASHBOARD
# =====================================================

def merchant_snapshot(merchant_id: int):

    stats = load_stats()
    m = stats.get(str(merchant_id), {})

    return {
        "total_sales": m.get("total_sales", 0),
        "orders": m.get("orders", 0),
        "weekly_sales": sum(
            s["amount"]
            for s in m.get("weekly_sales", [])
            if s["ts"] > time.time() - 7 * 86400
        ),
        "tier": "Elite" if commission_rate(merchant_id) == 0.03 else "Standard",
    }


# =====================================================
# STANDALONE TEST
# =====================================================

if __name__ == "__main__":

    print("🏆 Merchant engine online")

    record_sale(7, 2_000_000, True)
    record_sale(7, 14_000_000, True)

    print("National:", leaderboard())
    print("Weekly:", weekly_leaderboard())
    print("Snapshot:", merchant_snapshot(7))