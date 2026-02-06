"""
=====================================================
FLIPTRYBE SEGMENT 96
EMERGENCY ORCHESTRATOR
=====================================================

Purpose:
Unified high-authority control plane that can:

1. Halt all payments
2. Disable bookings
3. Freeze wallets
4. Stop rides
5. Lock shortlets
6. Suspend creators
7. Shutdown chat
8. Pause logistics
9. Region blackout
10. Feature blackout
11. Withdraw listings
12. Traffic isolation
13. Admin escalation
14. Regulatory freeze
15. Manual override
=====================================================
"""

from app.segments.segment_90_system_state_bus import GLOBAL_STATE_BUS
from app.segments.segment_93_incident_forensics import open_incident, add_event


# =====================================================
# CORE EMERGENCY OPS
# =====================================================

def activate_global_lockdown(reason: str):

    iid = open_incident("Global emergency", severity="critical")

    for flag in [
        "payments_enabled",
        "bookings_enabled",
        "wallets_enabled",
        "rides_enabled",
        "shortlets_enabled",
        "chat_enabled",
        "logistics_enabled",
    ]:
        GLOBAL_STATE_BUS.update("features", flag, False)

    GLOBAL_STATE_BUS.update("admin", "region_blackout", True)

    add_event(
        iid,
        "lockdown",
        "Platform frozen",
        {"reason": reason},
    )

    return iid


def lift_lockdown(incident_id: str):

    for flag in [
        "payments_enabled",
        "bookings_enabled",
        "wallets_enabled",
        "rides_enabled",
        "shortlets_enabled",
        "chat_enabled",
        "logistics_enabled",
    ]:
        GLOBAL_STATE_BUS.update("features", flag, True)

    GLOBAL_STATE_BUS.update("admin", "region_blackout", False)

    add_event(
        incident_id,
        "recovery",
        "Lockdown lifted",
        {},
    )


# =====================================================
# ADMIN TRIGGER
# =====================================================

def manual_trigger(reason):

    return activate_global_lockdown(reason)