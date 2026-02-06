"""
=====================================================
FLIPTRYBE SEGMENT 57
MERCHANT GROWTH & INCENTIVE SIMULATOR
=====================================================
Predicts sales growth under:
commission changes,
delivery incentives,
ranking boosts.
=====================================================
"""

import math
from dataclasses import dataclass
from typing import Dict

from app.segments.segment_47_merchant_performance import merchant_snapshot
from app.segments.segment_51_ads_analytics import aggregate_campaign_metrics


# =====================================================
# MODEL
# =====================================================

@dataclass
class GrowthScenario:

    commission_rate: float
    delivery_bonus: float
    rank_boost: float
    ad_spend_multiplier: float


# =====================================================
# FORECAST ENGINE
# =====================================================

def forecast_merchant(merchant_id: int, scenario: GrowthScenario):

    base = merchant_snapshot(merchant_id)

    weekly = base["weekly_sales"]
    orders = base["orders"]

    baseline_growth = weekly * 0.15

    incentive_factor = (
        (1 - scenario.commission_rate)
        + scenario.delivery_bonus
        + scenario.rank_boost
    )

    ad_factor = scenario.ad_spend_multiplier

    projected = weekly + (baseline_growth * incentive_factor * ad_factor)

    return {
        "current_weekly": weekly,
        "projected_weekly": round(projected, 2),
        "uplift_pct": round((projected - weekly) / max(1, weekly) * 100, 2),
    }


# =====================================================
# PORTFOLIO SIM
# =====================================================

def portfolio_simulation(scenarios: Dict[str, GrowthScenario], merchants):

    results = {}

    for name, scenario in scenarios.items():

        total = 0

        for mid in merchants:
            f = forecast_merchant(mid, scenario)
            total += f["projected_weekly"]

        results[name] = total

    return results


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    scenario = GrowthScenario(
        commission_rate=0.03,
        delivery_bonus=0.05,
        rank_boost=0.2,
        ad_spend_multiplier=1.3,
    )

    print(forecast_merchant(7, scenario))