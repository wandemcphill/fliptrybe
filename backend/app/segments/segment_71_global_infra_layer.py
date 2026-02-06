"""
=====================================================
FLIPTRYBE SEGMENT 71
GLOBAL INFRASTRUCTURE CONTROL PLANE
=====================================================
Responsibilities:
1. Region registry
2. Geo routing
3. Edge caching
4. Traffic shaping
5. Failover
6. SLO monitors
7. Incident tracking
8. Runbooks
9. Chaos testing
10. Cost optimizer
=====================================================
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List
import random
import uuid


# =====================================================
# REGION REGISTRY
# =====================================================

REGIONS = {
    "af-west": {"latency": 40, "healthy": True, "cost": 1.0},
    "eu-central": {"latency": 60, "healthy": True, "cost": 1.2},
    "us-east": {"latency": 110, "healthy": True, "cost": 1.5},
}


# =====================================================
# GEO ROUTER
# =====================================================

def pick_region(user_geo: str):

    candidates = [
        (r, meta) for r, meta in REGIONS.items()
        if meta["healthy"]
    ]

    return min(candidates, key=lambda x: x[1]["latency"])[0]


# =====================================================
# EDGE CACHE
# =====================================================

EDGE_CACHE: Dict[str, dict] = {}


def cache_edge(key: str, value: dict):

    EDGE_CACHE[key] = value


def get_edge(key: str):

    return EDGE_CACHE.get(key)


# =====================================================
# TRAFFIC SHAPER
# =====================================================

TRAFFIC_LIMITS = {
    "max_rps": 5000,
}


def allow_request(current_rps):

    return current_rps < TRAFFIC_LIMITS["max_rps"]


# =====================================================
# FAILOVER
# =====================================================

def failover(primary: str):

    REGIONS[primary]["healthy"] = False

    for r, meta in REGIONS.items():
        if meta["healthy"]:
            return r

    raise RuntimeError("All regions down")


# =====================================================
# SLO MONITOR
# =====================================================

@dataclass
class SLO:
    name: str
    target: float
    current: float = 100.0


SLOS: Dict[str, SLO] = {}


def update_slo(name: str, value: float):

    slo = SLOS.setdefault(name, SLO(name=name, target=99.9))

    slo.current = value


# =====================================================
# INCIDENT ENGINE
# =====================================================

@dataclass
class Incident:
    id: str
    title: str
    region: str
    severity: str
    opened_at: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False


INCIDENTS: Dict[str, Incident] = {}


def open_incident(title, region, severity):

    inc = Incident(
        id=str(uuid.uuid4()),
        title=title,
        region=region,
        severity=severity,
    )

    INCIDENTS[inc.id] = inc
    return inc


# =====================================================
# RUNBOOKS
# =====================================================

RUNBOOKS = {
    "db_down": "Restart replica, promote standby, invalidate cache",
    "latency_spike": "Shift traffic, scale edges, inspect queues",
}


def get_runbook(key):

    return RUNBOOKS.get(key, "No runbook")


# =====================================================
# CHAOS TESTING
# =====================================================

def inject_fault():

    region = random.choice(list(REGIONS.keys()))

    REGIONS[region]["healthy"] = False
    return region


# =====================================================
# COST OPTIMIZER
# =====================================================

def cheapest_region():

    return min(REGIONS.items(), key=lambda r: r[1]["cost"])[0]


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    print("ROUTE:", pick_region("NG"))

    region = inject_fault()

    print("CHAOS TOOK:", region)

    print("FAILOVER TO:", failover(region))

    inc = open_incident("DB outage", region, "high")

    print("INCIDENT:", inc)

    update_slo("api_latency", 98.1)

    print("SLOS:", SLOS)