"""
=====================================================
FLIPTRYBE SEGMENT 90
SYSTEM STATE BUS
=====================================================

Purpose:
Unified in-memory + pluggable backend fabric for
sharing runtime health, load, saturation, and
operational state across services.

Adds:
1. Global state registry
2. Thread-safe mutation
3. Health channel
4. Load channel
5. Error channel
6. Latency channel
7. Saturation channel
8. Capacity channel
9. Feature flag state
10. Region status
11. Dependency health
12. Rolling deploy markers
13. Incident state
14. Admin override signals
15. Snapshot export
=====================================================
"""

from threading import Lock
from typing import Dict, Any
from datetime import datetime
import json


# =====================================================
# CORE STATE STORE
# =====================================================

class SystemStateBus:

    def __init__(self):

        self._lock = Lock()
        self._state: Dict[str, Dict[str, Any]] = {
            "health": {},
            "load": {},
            "errors": {},
            "latency": {},
            "saturation": {},
            "capacity": {},
            "features": {},
            "regions": {},
            "dependencies": {},
            "deployments": {},
            "incidents": {},
            "admin": {},
        }

    # -------------------------------------------------

    def update(self, channel: str, key: str, value: Any):

        with self._lock:

            if channel not in self._state:
                raise KeyError(f"Unknown state channel: {channel}")

            self._state[channel][key] = {
                "value": value,
                "timestamp": datetime.utcnow().isoformat(),
            }

    # -------------------------------------------------

    def get(self, channel: str, key: str):

        with self._lock:
            return self._state.get(channel, {}).get(key)

    # -------------------------------------------------

    def channel_snapshot(self, channel: str):

        with self._lock:
            return dict(self._state.get(channel, {}))

    # -------------------------------------------------

    def full_snapshot(self):

        with self._lock:
            return json.loads(json.dumps(self._state))


# =====================================================
# SINGLETON BUS
# =====================================================

GLOBAL_STATE_BUS = SystemStateBus()


# =====================================================
# HELPERS
# =====================================================

def publish_health(service: str, healthy: bool):

    GLOBAL_STATE_BUS.update("health", service, healthy)


def publish_load(service: str, load: float):

    GLOBAL_STATE_BUS.update("load", service, load)


def publish_error(service: str, error_count: int):

    GLOBAL_STATE_BUS.update("errors", service, error_count)


def publish_latency(service: str, ms: float):

    GLOBAL_STATE_BUS.update("latency", service, ms)


def publish_feature_flag(flag: str, enabled: bool):

    GLOBAL_STATE_BUS.update("features", flag, enabled)


def region_status(region: str, online: bool):

    GLOBAL_STATE_BUS.update("regions", region, online)


# =====================================================
# EXPORT
# =====================================================

def export_state_json():

    snapshot = GLOBAL_STATE_BUS.full_snapshot()

    return json.dumps(snapshot, indent=2)