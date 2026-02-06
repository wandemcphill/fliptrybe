"""
=====================================================
FLIPTRYBE SEGMENT 59
ROUTE MONITOR & DEVIATION ENGINE
=====================================================
Tracks live routes,
detects divergence,
alerts buyers/admin,
requests reroute approval.
=====================================================
"""

import math
import time
from dataclasses import dataclass, field
from typing import List, Tuple


# =====================================================
# DATA MODELS
# =====================================================

@dataclass
class RoutePoint:
    lat: float
    lng: float
    ts: float


@dataclass
class ActiveRoute:
    order_id: int
    buyer_id: int
    driver_id: int
    planned_path: List[Tuple[float, float]]
    corridor_km: float = 1.0
    points: List[RoutePoint] = field(default_factory=list)
    last_alert_ts: float = 0


# =====================================================
# GEOMETRY
# =====================================================

def haversine(a, b):

    R = 6371

    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    h = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return 2 * R * math.asin(math.sqrt(h))


# =====================================================
# DEVIATION
# =====================================================

def min_distance_to_path(point, path):

    return min(haversine(point, p) for p in path)


def deviation_score(route: ActiveRoute):

    if not route.points:
        return 0

    p = route.points[-1]
    dist = min_distance_to_path((p.lat, p.lng), route.planned_path)

    return dist / route.corridor_km


# =====================================================
# INGEST POINT
# =====================================================

def ingest_point(route: ActiveRoute, lat: float, lng: float):

    rp = RoutePoint(lat=lat, lng=lng, ts=time.time())

    route.points.append(rp)

    score = deviation_score(route)

    if score > 1.2 and time.time() - route.last_alert_ts > 120:

        route.last_alert_ts = time.time()

        return {
            "alert": True,
            "order_id": route.order_id,
            "score": round(score, 2),
            "message": "Driver deviated from route",
        }

    return {"alert": False}


# =====================================================
# STOP DETECTION
# =====================================================

def detect_stop(route: ActiveRoute, window=300):

    if len(route.points) < 3:
        return False

    recent = route.points[-3:]

    d = sum(
        haversine(
            (recent[i].lat, recent[i].lng),
            (recent[i + 1].lat, recent[i + 1].lng),
        )
        for i in range(len(recent) - 1)
    )

    return d < 0.1 and time.time() - recent[0].ts > window


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    route = ActiveRoute(
        order_id=9,
        buyer_id=1,
        driver_id=7,
        planned_path=[(6.45, 3.39), (6.5, 3.4)],
    )

    print(ingest_point(route, 6.45, 3.39))
    print(ingest_point(route, 6.6, 3.6))  # deviation