"""
=====================================================
FLIPTRYBE SEGMENT 94
COST GOVERNOR
=====================================================

Purpose:
Tracks and governs:

1. Infra burn rate
2. API spend
3. Payment fees
4. Fraud loss
5. Driver incentives
6. Promo subsidies
7. Storage growth
8. Data egress
9. Compute saturation
10. Regional margins
11. Feature cost attribution
12. Experiment budgets
13. Incident cost
14. SLA penalties
15. Runaway detection
=====================================================
"""

from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime
import uuid


# =====================================================
# DATA MODELS
# =====================================================

@dataclass
class CostEvent:
    id: str
    category: str
    service: str
    region: str
    amount: float
    currency: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Budget:
    id: str
    name: str
    limit: float
    spent: float = 0.0
    alert_threshold: float = 0.8


COST_EVENTS: List[CostEvent] = []
BUDGETS: Dict[str, Budget] = {}


# =====================================================
# CORE OPS
# =====================================================

def record_cost(category, service, region, amount, currency="USD"):

    ev = CostEvent(
        id=uuid.uuid4().hex,
        category=category,
        service=service,
        region=region,
        amount=amount,
        currency=currency,
    )

    COST_EVENTS.append(ev)

    for b in BUDGETS.values():
        b.spent += amount


def create_budget(name, limit):

    bid = uuid.uuid4().hex

    BUDGETS[bid] = Budget(
        id=bid,
        name=name,
        limit=limit,
    )

    return bid


# =====================================================
# GOVERNANCE
# =====================================================

def budgets_exceeded():

    return [
        b for b in BUDGETS.values()
        if b.spent >= b.limit
    ]


def budgets_near_limit():

    return [
        b for b in BUDGETS.values()
        if b.spent >= b.limit * b.alert_threshold
    ]


def runaway_services():

    agg: Dict[str, float] = {}

    for ev in COST_EVENTS:
        agg.setdefault(ev.service, 0.0)
        agg[ev.service] += ev.amount

    return sorted(agg.items(), key=lambda x: x[1], reverse=True)


# =====================================================
# REPORTING
# =====================================================

def cost_snapshot():

    return {
        "total_events": len(COST_EVENTS),
        "budgets": {
            b.name: {
                "limit": b.limit,
                "spent": b.spent,
            }
            for b in BUDGETS.values()
        },
        "top_services": runaway_services()[:5],
    }