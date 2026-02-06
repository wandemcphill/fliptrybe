"""
=====================================================
FLIPTRYBE SEGMENT 91
AUTONOMIC CONTROL PLANE
=====================================================

Purpose:
Continuously monitors the SystemStateBus and triggers
mitigations, scale actions, freezes, reroutes, and
audit escalation automatically.

Subsystems:
1. Policy registry
2. Condition evaluator
3. Action engine
4. Scaling triggers
5. Circuit breaker flips
6. Region failover
7. Fraud freezes
8. Compliance escalation
9. Feature kill-switch
10. Rate-limit activation
11. Traffic shedding
12. Warm-pool spinup
13. Incident creation
14. Pager hooks (stub)
15. Manual override
=====================================================
"""

import threading
import time
from typing import Callable, Dict, Any, List

from app.segments.segment_90_system_state_bus import GLOBAL_STATE_BUS
from app.segments.segment_87_risk_audit_registry import register_risk


# =====================================================
# POLICY MODEL
# =====================================================

PolicyCondition = Callable[[SystemStateBus], bool]
PolicyAction = Callable[[], None]


class AutonomicPolicy:

    def __init__(self, name, condition: PolicyCondition, action: PolicyAction):

        self.name = name
        self.condition = condition
        self.action = action


POLICIES: List[AutonomicPolicy] = []


def register_policy(policy: AutonomicPolicy):

    POLICIES.append(policy)


# =====================================================
# ACTIONS
# =====================================================

def freeze_payments():

    GLOBAL_STATE_BUS.update("admin", "payments_frozen", True)


def escalate_compliance():

    register_risk(
        "Runtime compliance incident",
        "Autonomic engine escalated issue at runtime.",
        "high",
        "runtime"
    )


def enable_kill_switch():

    GLOBAL_STATE_BUS.update("features", "global_kill_switch", True)


def open_incident(title: str):

    GLOBAL_STATE_BUS.update("incidents", title, {"open": True})


# =====================================================
# EVALUATION LOOP
# =====================================================

class AutonomicController(threading.Thread):

    daemon = True

    def __init__(self, interval=5):

        super().__init__()
        self.interval = interval
        self._stop = False

    def run(self):

        while not self._stop:

            for p in POLICIES:
                try:
                    if p.condition(GLOBAL_STATE_BUS):
                        p.action()
                except Exception as e:
                    open_incident(f"Autonomic failure: {e}")

            time.sleep(self.interval)

    def stop(self):

        self._stop = True


# =====================================================
# DEFAULT POLICIES
# =====================================================

def high_error_rate(bus):

    errors = bus.channel_snapshot("errors")

    return any(v["value"] > 100 for v in errors.values())


def excessive_latency(bus):

    latency = bus.channel_snapshot("latency")

    return any(v["value"] > 2000 for v in latency.values())


register_policy(
    AutonomicPolicy(
        "FreezePaymentsOnErrors",
        high_error_rate,
        freeze_payments,
    )
)

register_policy(
    AutonomicPolicy(
        "KillSwitchOnLatency",
        excessive_latency,
        enable_kill_switch,
    )
)


# =====================================================
# BOOT
# =====================================================

def start_autonomic():

    controller = AutonomicController()
    controller.start()
    return controller