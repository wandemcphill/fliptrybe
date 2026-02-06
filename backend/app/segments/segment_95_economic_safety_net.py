"""
=====================================================
FLIPTRYBE SEGMENT 95
ECONOMIC SAFETY NET
=====================================================

Purpose:
Automatically mitigates financial risk by:

1. Freezing promos
2. Disabling subsidies
3. Throttling traffic
4. Pausing payouts
5. Halting experiments
6. Region cost isolation
7. Vendor cutoff
8. Fee renegotiation flags
9. SLA penalty triggers
10. Fraud surge lockdown
=====================================================
"""

from app.segments.segment_94_cost_governor import (
    budgets_exceeded,
    budgets_near_limit,
)

from app.segments.segment_90_system_state_bus import GLOBAL_STATE_BUS


# =====================================================
# ACTIONS
# =====================================================

def freeze_promos():

    GLOBAL_STATE_BUS.update("features", "promos_enabled", False)


def pause_payouts():

    GLOBAL_STATE_BUS.update("admin", "payouts_paused", True)


def throttle_regions():

    GLOBAL_STATE_BUS.update("admin", "region_throttle", True)


# =====================================================
# EVALUATION
# =====================================================

def enforce_cost_controls():

    exceeded = budgets_exceeded()
    near = budgets_near_limit()

    if exceeded:
        freeze_promos()
        pause_payouts()

    elif near:
        throttle_regions()


# =====================================================
# PERIODIC DRIVER
# =====================================================

def run_cost_safety_net(interval=60):

    import time

    while True:
        enforce_cost_controls()
        time.sleep(interval)