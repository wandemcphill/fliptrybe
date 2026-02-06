"""
=====================================================
FLIPTRYBE SEGMENT 51
ADS ANALYTICS & INTELLIGENCE LAYER
=====================================================
Produces:
ROI dashboards,
geo/category heatmaps,
budget pacing curves,
anomaly alerts.
=====================================================
"""

import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List

from app.segments.segment_49_ads_engine import CLICK_LOG
from app.segments.segment_50_ads_billing import INVOICES, WALLETS


# =====================================================
# METRICS STRUCTURE
# =====================================================

@dataclass
class CampaignMetrics:

    campaign_id: int
    impressions: int = 0
    clicks: int = 0
    spend: float = 0.0
    revenue: float = 0.0

    @property
    def ctr(self):
        return self.clicks / self.impressions if self.impressions else 0

    @property
    def roi(self):
        if self.spend == 0:
            return 0
        return (self.revenue - self.spend) / self.spend


# =====================================================
# AGGREGATORS
# =====================================================

def aggregate_campaign_metrics():

    metrics: Dict[int, CampaignMetrics] = {}

    for click in CLICK_LOG:

        cid = click["campaign_id"]

        if cid not in metrics:
            metrics[cid] = CampaignMetrics(campaign_id=cid)

        m = metrics[cid]
        m.clicks += 1
        m.spend += click["cpc"]

    return metrics


def merge_revenue(
    metrics: Dict[int, CampaignMetrics],
    revenue_map: Dict[int, float],
):

    for cid, rev in revenue_map.items():
        if cid in metrics:
            metrics[cid].revenue += rev

    return metrics


# =====================================================
# GEO HEATMAP
# =====================================================

def geo_heatmap():

    geo = defaultdict(int)

    for click in CLICK_LOG:
        geo[click["geo"]] += 1

    return dict(geo)


# =====================================================
# CATEGORY PERFORMANCE
# =====================================================

def category_performance():

    cats = defaultdict(int)

    for click in CLICK_LOG:
        cats[click["category"]] += 1

    return dict(cats)


# =====================================================
# BUDGET PACING
# =====================================================

def pacing_curve(campaign_id: int):

    times = [
        c["ts"]
        for c in CLICK_LOG
        if c["campaign_id"] == campaign_id
    ]

    if not times:
        return []

    start = min(times)
    end = max(times)

    buckets = defaultdict(int)

    for t in times:
        bucket = int((t - start) / 3600)
        buckets[bucket] += 1

    return sorted(buckets.items())


# =====================================================
# ANOMALY DETECTION
# =====================================================

def detect_spend_spikes():

    spends = defaultdict(list)

    for click in CLICK_LOG:
        spends[click["campaign_id"]].append(click["cpc"])

    alerts = []

    for cid, values in spends.items():

        if len(values) < 5:
            continue

        avg = statistics.mean(values)
        stdev = statistics.stdev(values)

        for v in values:
            if v > avg + (3 * stdev):
                alerts.append(
                    {
                        "campaign_id": cid,
                        "value": v,
                        "avg": avg,
                    }
                )

    return alerts


# =====================================================
# MERCHANT DASHBOARD
# =====================================================

def merchant_dashboard(merchant_id: int):

    wallet = WALLETS.get(merchant_id)

    invoices = [
        inv
        for inv in INVOICES.values()
        if inv.merchant_id == merchant_id
    ]

    total_spend = sum(inv.amount for inv in invoices)

    campaigns = aggregate_campaign_metrics()

    my_campaigns = {
        cid: m
        for cid, m in campaigns.items()
        if cid in [i.line_items[0]["campaign_id"] for i in invoices]
    }

    return {
        "wallet_balance": wallet.balance if wallet else 0,
        "total_spend": total_spend,
        "campaigns": my_campaigns,
        "geo_map": geo_heatmap(),
        "categories": category_performance(),
        "alerts": detect_spend_spikes(),
    }


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    from app.segments.segment_50_ads_billing import fund_wallet
    from app.segments.segment_49_ads_engine import AdCampaign, serve_ad

    fund_wallet(5, 20000)

    camp = AdCampaign(
        campaign_id=22,
        merchant_id=5,
        listing_id=101,
        max_cpc=300,
        daily_budget=8000,
        geo_targets=["abuja"],
        categories=["laptops"],
    )

    for _ in range(10):
        serve_ad(camp, geo="abuja", category="laptops")

    dash = merchant_dashboard(5)

    print("DASHBOARD:")
    for k, v in dash.items():
        print(k, v)