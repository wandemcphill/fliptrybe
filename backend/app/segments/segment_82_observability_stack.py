"""
=====================================================
FLIPTRYBE SEGMENT 82
OBSERVABILITY & TELEMETRY STACK
=====================================================
Responsibilities:
1. Structured logging
2. Log shipping
3. Trace IDs
4. Span recording
5. Metrics counters
6. Histograms
7. Error tracking
8. Alert rules
9. On-call routing
10. SLA monitoring
11. SLO budgets
12. Dashboard snapshots
13. Audit logs
14. Anomaly detection
15. Incident lifecycle
=====================================================
"""

import uuid
import time
from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime
import statistics


# =====================================================
# 1. STRUCTURED LOGGING
# =====================================================

LOGS: List[Dict] = []


def log(level: str, message: str, **ctx):

    entry = {
        "ts": datetime.utcnow().isoformat(),
        "level": level,
        "msg": message,
        "ctx": ctx,
    }

    LOGS.append(entry)
    print(entry)


# =====================================================
# 2. LOG SHIPPING
# =====================================================

LOG_SINKS: List[str] = []


def ship_logs():

    count = len(LOGS)
    LOGS.clear()
    return count


# =====================================================
# 3. TRACE IDS
# =====================================================

def new_trace_id() -> str:
    return uuid.uuid4().hex


# =====================================================
# 4. SPAN RECORDING
# =====================================================

@dataclass
class Span:
    trace_id: str
    name: str
    start: float = field(default_factory=time.time)
    end: float | None = None


SPANS: List[Span] = []


def start_span(trace_id: str, name: str):

    span = Span(trace_id, name)
    SPANS.append(span)
    return span


def end_span(span: Span):
    span.end = time.time()


# =====================================================
# 5. METRICS COUNTERS
# =====================================================

COUNTERS: Dict[str, int] = {}


def inc_metric(name: str, value=1):
    COUNTERS[name] = COUNTERS.get(name, 0) + value


# =====================================================
# 6. HISTOGRAMS
# =====================================================

HISTOGRAMS: Dict[str, List[float]] = {}


def observe(name: str, value: float):

    HISTOGRAMS.setdefault(name, []).append(value)


# =====================================================
# 7. ERROR TRACKING
# =====================================================

ERRORS: List[Dict] = []


def record_error(exc: Exception, trace_id: str):

    ERRORS.append({
        "type": type(exc).__name__,
        "msg": str(exc),
        "trace": trace_id,
        "ts": datetime.utcnow().isoformat(),
    })


# =====================================================
# 8. ALERT RULES
# =====================================================

ALERT_RULES: Dict[str, float] = {
    "error_rate": 0.1,
}


def evaluate_alerts():

    alerts = []

    total = COUNTERS.get("requests", 0)
    errors = COUNTERS.get("errors", 0)

    rate = errors / max(total, 1)

    if rate > ALERT_RULES["error_rate"]:
        alerts.append("High error rate")

    return alerts


# =====================================================
# 9. ON CALL ROUTING
# =====================================================

ON_CALL = ["ops1", "ops2"]


def page_on_call(alert: str):

    return random.choice(ON_CALL)


# =====================================================
# 10. SLA MONITORING
# =====================================================

SLA_TARGETS = {"latency_p95": 500}


def sla_breach():

    p95 = percentile(HISTOGRAMS.get("latency", []), 95)

    return p95 and p95 > SLA_TARGETS["latency_p95"]


# =====================================================
# 11. SLO BUDGETS
# =====================================================

SLO_BUDGETS: Dict[str, float] = {"availability": 0.999}


# =====================================================
# 12. DASHBOARD SNAPSHOT
# =====================================================

def dashboard_snapshot():

    return {
        "metrics": COUNTERS,
        "histograms": {k: len(v) for k, v in HISTOGRAMS.items()},
        "errors": len(ERRORS),
    }


# =====================================================
# 13. AUDIT LOGS
# =====================================================

AUDIT_LOGS: List[Dict] = []


def audit(action: str, user_id=None, resource=None):

    AUDIT_LOGS.append({
        "action": action,
        "user_id": user_id,
        "resource": resource,
        "ts": datetime.utcnow().isoformat(),
    })


# =====================================================
# 14. ANOMALY DETECTION
# =====================================================

def detect_anomaly(metric: str):

    values = HISTOGRAMS.get(metric, [])

    if len(values) < 10:
        return False

    mean = statistics.mean(values)
    stdev = statistics.stdev(values)

    return values[-1] > mean + 3 * stdev


# =====================================================
# 15. INCIDENT LIFECYCLE
# =====================================================

INCIDENTS: List[Dict] = []


def open_incident(title: str):

    incident = {
        "id": uuid.uuid4().hex,
        "title": title,
        "opened": datetime.utcnow().isoformat(),
        "status": "open",
    }

    INCIDENTS.append(incident)
    return incident


def close_incident(incident_id: str):

    for i in INCIDENTS:
        if i["id"] == incident_id:
            i["status"] = "closed"
            i["closed"] = datetime.utcnow().isoformat()


# =====================================================
# HELPERS
# =====================================================

def percentile(data: List[float], p: int):

    if not data:
        return None

    data = sorted(data)
    k = int(len(data) * p / 100)
    return data[min(k, len(data) - 1)]


# =====================================================
# SELF TEST
# =====================================================

if __name__ == "__main__":

    trace = new_trace_id()

    span = start_span(trace, "request")
    time.sleep(0.01)
    end_span(span)

    inc_metric("requests")
    inc_metric("errors")

    observe("latency", 600)

    print("Alerts:", evaluate_alerts())
    print("SLA breach:", sla_breach())
    print("Dashboard:", dashboard_snapshot())