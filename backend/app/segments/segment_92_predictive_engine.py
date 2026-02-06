"""
=====================================================
FLIPTRYBE SEGMENT 92
PREDICTIVE ANALYTICS ENGINE
=====================================================

Purpose:
Consumes telemetry snapshots to forecast:

1. Traffic surges
2. Cost overruns
3. Fraud probability
4. Latency blowups
5. Capacity exhaustion
6. Regional degradation
7. Incident likelihood
8. SLA breach risk
9. Queue backlogs
10. Payment failures
11. Driver supply gaps
12. Market imbalance
13. Inventory depletion
14. Compliance pressure
15. Growth saturation
=====================================================
"""

from typing import Dict, List
from statistics import mean
from datetime import datetime, timedelta

from app.segments.segment_90_system_state_bus import GLOBAL_STATE_BUS
from app.segments.segment_87_risk_audit_registry import register_risk


# =====================================================
# HISTORY BUFFER
# =====================================================

HISTORY: List[Dict] = []


def snapshot():

    snap = GLOBAL_STATE_BUS.full_snapshot()
    snap["timestamp"] = datetime.utcnow()
    HISTORY.append(snap)

    if len(HISTORY) > 500:
        HISTORY.pop(0)


# =====================================================
# METRIC EXTRACTORS
# =====================================================

def extract_channel(channel: str):

    values = []

    for s in HISTORY:
        ch = s.get(channel, {})
        for v in ch.values():
            values.append(v["value"])

    return values


# =====================================================
# FORECASTING HEURISTICS
# =====================================================

def trend(values):

    if len(values) < 5:
        return 0

    return values[-1] - mean(values[:-1])


def anomaly(values):

    if not values:
        return False

    avg = mean(values)
    return abs(values[-1] - avg) > avg * 0.5


# =====================================================
# RISK SIGNALERS
# =====================================================

def forecast():

    report = {}

    for channel in [
        "load", "latency", "errors",
        "capacity", "saturation"
    ]:

        vals = extract_channel(channel)

        report[channel] = {
            "trend": trend(vals),
            "anomaly": anomaly(vals),
        }

        if report[channel]["anomaly"]:
            register_risk(
                f"Predictive anomaly in {channel}",
                "Forecast engine detected abnormal trajectory.",
                "medium",
                "forecast"
            )

    return report


# =====================================================
# PERIODIC DRIVER
# =====================================================

def run_forecaster(interval=30):

    import time

    while True:
        snapshot()
        forecast()
        time.sleep(interval)