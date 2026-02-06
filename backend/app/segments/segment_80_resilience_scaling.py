"""
=====================================================
FLIPTRYBE SEGMENT 80
RESILIENCE & SCALE ORCHESTRATION ENGINE
=====================================================
Responsibilities:
1. Health probes
2. Circuit breakers
3. Rate limiting
4. Backpressure
5. Traffic shaping
6. Auto scaling
7. Cold start detection
8. Warm pools
9. Multi-region routing
10. Failover
11. Chaos testing
12. Cost governance
13. Budget alerts
14. FinOps dashboards
15. Capacity planning
=====================================================
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random


# =====================================================
# 1. HEALTH MONITORING
# =====================================================

@dataclass
class HealthProbe:
    service: str
    healthy: bool = True
    last_checked: datetime = field(default_factory=datetime.utcnow)


HEALTH_PROBES: Dict[str, HealthProbe] = {}


def check_health(service: str) -> HealthProbe:
    probe = HEALTH_PROBES.setdefault(service, HealthProbe(service))
    probe.last_checked = datetime.utcnow()
    probe.healthy = random.random() > 0.05
    return probe


# =====================================================
# 2. CIRCUIT BREAKERS
# =====================================================

@dataclass
class CircuitBreaker:
    service: str
    failures: int = 0
    open_until: Optional[datetime] = None


BREAKERS: Dict[str, CircuitBreaker] = {}


def allow_request(service: str) -> bool:
    breaker = BREAKERS.setdefault(service, CircuitBreaker(service))
    if breaker.open_until and datetime.utcnow() < breaker.open_until:
        return False
    return True


def record_failure(service: str):
    breaker = BREAKERS.setdefault(service, CircuitBreaker(service))
    breaker.failures += 1
    if breaker.failures >= 5:
        breaker.open_until = datetime.utcnow() + timedelta(seconds=30)


# =====================================================
# 3. RATE LIMITING
# =====================================================

RATE_BUCKETS: Dict[str, List[datetime]] = {}


def rate_limit(key: str, limit=100, window=60) -> bool:
    now = datetime.utcnow()
    bucket = RATE_BUCKETS.setdefault(key, [])
    bucket[:] = [t for t in bucket if (now - t).seconds < window]
    if len(bucket) >= limit:
        return False
    bucket.append(now)
    return True


# =====================================================
# 4. BACKPRESSURE
# =====================================================

QUEUE_DEPTH: Dict[str, int] = {}


def apply_backpressure(queue: str, max_depth=500) -> bool:
    depth = QUEUE_DEPTH.get(queue, 0)
    return depth > max_depth


# =====================================================
# 5. TRAFFIC SHAPING
# =====================================================

def choose_backend(backends: Dict[str, int]) -> str:
    total = sum(backends.values())
    r = random.randint(1, total)
    upto = 0
    for name, weight in backends.items():
        upto += weight
        if upto >= r:
            return name
    return list(backends.keys())[0]


# =====================================================
# 6. AUTO SCALING
# =====================================================

@dataclass
class AutoScaler:
    service: str
    replicas: int = 1
    cpu_load: float = 0.0


SCALERS: Dict[str, AutoScaler] = {}


def scale_service(service: str) -> int:
    scaler = SCALERS.setdefault(service, AutoScaler(service))
    if scaler.cpu_load > 0.75:
        scaler.replicas += 1
    elif scaler.cpu_load < 0.20 and scaler.replicas > 1:
        scaler.replicas -= 1
    return scaler.replicas


# =====================================================
# 7. COLD START DETECTION
# =====================================================

LAST_ACTIVITY: Dict[str, datetime] = {}


def cold_start(service: str, threshold=300) -> bool:
    last = LAST_ACTIVITY.get(service)
    if not last:
        return True
    return (datetime.utcnow() - last).seconds > threshold


# =====================================================
# 8. WARM POOLS
# =====================================================

WARM_POOLS: Dict[str, int] = {}


def reserve_warm_pool(service: str, size=2):
    WARM_POOLS[service] = max(WARM_POOLS.get(service, 0), size)


# =====================================================
# 9. MULTI REGION ROUTING
# =====================================================

REGION_HEALTH: Dict[str, bool] = {
    "us-east": True,
    "eu-west": True,
    "africa-south": True,
}


def pick_region() -> str:
    healthy = [r for r, ok in REGION_HEALTH.items() if ok]
    return random.choice(healthy)


# =====================================================
# 10. FAILOVER
# =====================================================

def failover_region(region: str) -> str:
    REGION_HEALTH[region] = False
    return pick_region()


# =====================================================
# 11. CHAOS TESTING
# =====================================================

def inject_fault(service: str) -> bool:
    if random.random() < 0.2:
        record_failure(service)
        return True
    return False


# =====================================================
# 12. COST GOVERNANCE
# =====================================================

COSTS: Dict[str, float] = {}


def add_cost(service: str, amount: float):
    COSTS[service] = COSTS.get(service, 0) + amount


# =====================================================
# 13. BUDGET ALERTS
# =====================================================

BUDGETS: Dict[str, float] = {}


def budget_alert(service: str) -> bool:
    budget = BUDGETS.get(service)
    return bool(budget and COSTS.get(service, 0) > budget)


# =====================================================
# 14. FINOPS DASHBOARD
# =====================================================

def finops_snapshot():
    return {
        "costs": COSTS.copy(),
        "budgets": BUDGETS.copy(),
        "replicas": {k: v.replicas for k, v in SCALERS.items()},
        "warm_pools": WARM_POOLS.copy(),
    }


# =====================================================
# 15. CAPACITY PLANNING
# =====================================================

def capacity_forecast(service: str) -> int:
    scaler = SCALERS.get(service)
    if not scaler:
        return 1
    projected = scaler.replicas + int(scaler.cpu_load * 5)
    return max(1, projected)


# =====================================================
# SELF TEST
# =====================================================

if __name__ == "__main__":

    print("Health:", check_health("payments"))

    reserve_warm_pool("payments", 3)

    SCALERS["payments"] = AutoScaler("payments", 2, 0.9)
    print("Scale:", scale_service("payments"))

    add_cost("payments", 200)
    BUDGETS["payments"] = 150

    print("Budget breach:", budget_alert("payments"))
    print("FinOps:", finops_snapshot())