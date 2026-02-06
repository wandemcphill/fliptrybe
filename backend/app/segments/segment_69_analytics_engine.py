"""
=====================================================
FLIPTRYBE SEGMENT 69
ANALYTICS & INTELLIGENCE ENGINE
=====================================================
Responsibilities:
1. Event ingestion
2. User cohorting
3. Funnel tracking
4. Attribution
5. LTV computation
6. Churn detection
7. Realtime dashboards
8. Export rails
9. Privacy masking
10. Retention signals
=====================================================
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
import csv
import io


# =====================================================
# MODELS
# =====================================================

@dataclass
class Event:
    id: str
    user_id: int
    type: str
    properties: dict
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Cohort:
    name: str
    user_ids: List[int]


@dataclass
class FunnelStep:
    name: str
    count: int = 0


@dataclass
class RetentionFlag:
    user_id: int
    risk: str
    created_at: datetime = field(default_factory=datetime.utcnow)


# =====================================================
# STORES
# =====================================================

EVENTS: List[Event] = []
RETENTION: Dict[int, RetentionFlag] = {}
COHORTS: Dict[str, Cohort] = {}


# =====================================================
# INGESTION
# =====================================================

def ingest_event(user_id: int, type: str, properties: dict):

    ev = Event(
        id=str(uuid.uuid4()),
        user_id=user_id,
        type=type,
        properties=properties,
    )

    EVENTS.append(ev)
    return ev


# =====================================================
# COHORT ENGINE
# =====================================================

def build_cohort(name: str, predicate):

    ids = list({e.user_id for e in EVENTS if predicate(e)})

    cohort = Cohort(name=name, user_ids=ids)

    COHORTS[name] = cohort
    return cohort


# =====================================================
# FUNNEL ENGINE
# =====================================================

FUNNELS: Dict[str, List[FunnelStep]] = {}


def define_funnel(name: str, steps: List[str]):

    FUNNELS[name] = [FunnelStep(step) for step in steps]


def compute_funnel(name: str):

    steps = FUNNELS[name]

    for step in steps:
        step.count = len([e for e in EVENTS if e.type == step.name])

    return steps


# =====================================================
# ATTRIBUTION
# =====================================================

def attribute_conversion(user_id: int):

    evs = [e for e in EVENTS if e.user_id == user_id]

    if not evs:
        return None

    return evs[0].type


# =====================================================
# LTV
# =====================================================

def compute_ltv(user_id: int):

    tx = [
        e for e in EVENTS
        if e.user_id == user_id and e.type == "purchase"
    ]

    return sum(e.properties.get("amount", 0) for e in tx)


# =====================================================
# CHURN
# =====================================================

def detect_churn(days=30):

    cutoff = datetime.utcnow() - timedelta(days=days)

    inactive = {}

    for e in EVENTS:
        inactive.setdefault(e.user_id, e.timestamp)

    for uid, last in inactive.items():
        if last < cutoff:
            RETENTION[uid] = RetentionFlag(uid, "churn-risk")

    return RETENTION


# =====================================================
# DASHBOARD
# =====================================================

def dashboard_snapshot():

    return {
        "events": len(EVENTS),
        "users": len({e.user_id for e in EVENTS}),
        "cohorts": {k: len(v.user_ids) for k, v in COHORTS.items()},
        "retention_flags": len(RETENTION),
    }


# =====================================================
# EXPORT
# =====================================================

def export_events_csv():

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["id", "user_id", "type", "timestamp"])

    for e in EVENTS:
        writer.writerow([
            e.id,
            e.user_id,
            e.type,
            e.timestamp.isoformat(),
        ])

    return output.getvalue()


# =====================================================
# PRIVACY MASK
# =====================================================

def anonymize_user(user_id: int):

    for e in EVENTS:
        if e.user_id == user_id:
            e.user_id = 0

    RETENTION.pop(user_id, None)


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    ingest_event(1, "signup", {})
    ingest_event(1, "purchase", {"amount": 2000})
    ingest_event(2, "signup", {})
    ingest_event(2, "view", {})

    define_funnel("checkout", ["signup", "purchase"])
    print("FUNNEL:", compute_funnel("checkout"))

    print("LTV:", compute_ltv(1))

    detect_churn(0)

    print("DASHBOARD:", dashboard_snapshot())