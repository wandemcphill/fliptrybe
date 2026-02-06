"""
=====================================================
FLIPTRYBE SEGMENT 43
PRODUCTION TELEMETRY + SLO ENGINE
=====================================================
Exports runtime metrics, tracks error budgets,
and emits alerts when thresholds are breached.
=====================================================
"""

import os
import time
import json
import threading
import statistics
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = Path.cwd()
METRIC_FILE = ROOT / ".telemetry.json"
ALERT_FILE = ROOT / ".alerts.log"
AUDIT_LOG = ROOT / "audit.log"

SLO = {
    "availability": 0.995,
    "p95_latency_ms": 600,
    "error_rate": 0.01,
}


# =====================================================
# STORAGE
# =====================================================

def load_metrics():
    if METRIC_FILE.exists():
        return json.loads(METRIC_FILE.read_text())
    return {
        "requests": [],
        "errors": [],
        "latencies": [],
    }


def save_metrics(metrics):
    METRIC_FILE.write_text(json.dumps(metrics, indent=2))


def audit(event, payload=None):

    entry = {
        "time": time.time(),
        "event": event,
        "payload": payload or {},
    }

    with open(AUDIT_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def alert(kind, message):

    record = {
        "time": time.time(),
        "kind": kind,
        "message": message,
    }

    with open(ALERT_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")

    audit("alert", record)


# =====================================================
# COLLECTORS
# =====================================================

def record_request(latency_ms, success=True):

    metrics = load_metrics()

    metrics["requests"].append(time.time())
    metrics["latencies"].append(latency_ms)

    if not success:
        metrics["errors"].append(time.time())

    save_metrics(metrics)


# =====================================================
# SLO ENGINE
# =====================================================

def evaluate_slo():

    metrics = load_metrics()

    now = time.time()
    window = 3600  # last hour

    reqs = [t for t in metrics["requests"] if t > now - window]
    errs = [t for t in metrics["errors"] if t > now - window]
    lats = metrics["latencies"][-200:]

    availability = 1 - (len(errs) / max(1, len(reqs)))
    p95 = statistics.quantiles(lats, n=20)[18] if len(lats) > 20 else 0

    breached = []

    if availability < SLO["availability"]:
        breached.append(("availability", availability))

    if p95 > SLO["p95_latency_ms"]:
        breached.append(("latency", p95))

    if len(errs) / max(1, len(reqs)) > SLO["error_rate"]:
        breached.append(("error_rate", len(errs) / max(1, len(reqs))))

    return breached


# =====================================================
# BACKGROUND WATCHER
# =====================================================

def slo_watcher():

    while True:
        breached = evaluate_slo()
        if breached:
            for name, value in breached:
                alert("slo_breach", f"{name}: {value}")
        time.sleep(30)


# =====================================================
# HTTP EXPORTER (Render health compatible)
# =====================================================

class TelemetryHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path == "/metrics":

            metrics = load_metrics()

            payload = {
                "slo": SLO,
                "current": {
                    "requests": len(metrics["requests"]),
                    "errors": len(metrics["errors"]),
                },
            }

            body = json.dumps(payload).encode()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        else:
            self.send_response(404)
            self.end_headers()


# =====================================================
# STARTUP
# =====================================================

def start():

    audit("telemetry_start")

    threading.Thread(target=slo_watcher, daemon=True).start()

    server = HTTPServer(("0.0.0.0", 9400), TelemetryHandler)

    print("📊 Telemetry exporter listening on :9400")

    server.serve_forever()


if __name__ == "__main__":
    start()