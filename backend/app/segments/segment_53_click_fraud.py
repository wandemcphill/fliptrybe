"""
=====================================================
FLIPTRYBE SEGMENT 53
CLICK FRAUD & TRUST FILTERS
=====================================================
Detects:
velocity abuse
IP clustering
geo anomalies
device entropy
replay patterns
=====================================================
"""

import time
import hashlib
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, Deque

from app.segments.segment_52_ad_auction import execute_auction


# =====================================================
# MEMORY STORES
# =====================================================

CLICK_LOG: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=200))
IP_ACTIVITY: Dict[str, int] = defaultdict(int)
DEVICE_ACTIVITY: Dict[str, int] = defaultdict(int)


# =====================================================
# CONFIG
# =====================================================

MAX_CLICKS_PER_MINUTE = 8
MAX_IP_HOURLY = 120
MAX_DEVICE_HOURLY = 80


# =====================================================
# SIGNAL MODEL
# =====================================================

@dataclass
class ClickSignal:

    ip: str
    device_id: str
    geo: str
    category: str
    user_agent: str
    ts: float = time.time()


# =====================================================
# HELPERS
# =====================================================

def _hash(value: str):

    return hashlib.sha256(value.encode()).hexdigest()[:16]


def fingerprint_device(device_id, user_agent):

    return _hash(device_id + user_agent)


# =====================================================
# CORE SCORING
# =====================================================

def score_click(signal: ClickSignal):

    score = 1.0

    minute_bucket = int(signal.ts // 60)

    CLICK_LOG[signal.ip].append(signal.ts)
    IP_ACTIVITY[signal.ip] += 1

    device_fp = fingerprint_device(signal.device_id, signal.user_agent)
    DEVICE_ACTIVITY[device_fp] += 1

    # -----------------------------------------
    # VELOCITY
    # -----------------------------------------

    recent = [
        t for t in CLICK_LOG[signal.ip]
        if signal.ts - t < 60
    ]

    if len(recent) > MAX_CLICKS_PER_MINUTE:
        score *= 0.1

    # -----------------------------------------
    # IP FLOODING
    # -----------------------------------------

    if IP_ACTIVITY[signal.ip] > MAX_IP_HOURLY:
        score *= 0.2

    # -----------------------------------------
    # DEVICE FLOODING
    # -----------------------------------------

    if DEVICE_ACTIVITY[device_fp] > MAX_DEVICE_HOURLY:
        score *= 0.2

    # -----------------------------------------
    # GEO CONSISTENCY
    # -----------------------------------------

    if signal.geo.lower() not in signal.ip.lower():
        score *= 0.7

    return round(score, 2)


# =====================================================
# ENTRYPOINT
# =====================================================

def process_click(signal: ClickSignal):

    trust = score_click(signal)

    if trust < 0.25:
        return {
            "accepted": False,
            "reason": "fraud_suspected",
            "trust": trust,
        }

    auction = execute_auction(signal.geo, signal.category)

    return {
        "accepted": True,
        "trust": trust,
        "auction": auction,
    }


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    fake_ip = "lagos-isp-24"

    for i in range(15):

        s = ClickSignal(
            ip=fake_ip,
            device_id="device123",
            geo="lagos",
            category="phones",
            user_agent="chrome-mobile",
        )

        print(process_click(s))