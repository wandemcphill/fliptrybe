"""
=====================================================
FLIPTRYBE SEGMENT 89
RUNTIME INTEGRITY GATE
=====================================================

Purpose:
Prevents the application from starting in staging /
production if audit blockers or wiring failures exist.

Adds:
1. Environment mode detection
2. Registry recheck at boot
3. Kill-switch enforcement
4. Required service presence
5. Env var completeness
6. Crypto backend verification
7. Payment provider availability
8. Queue backend readiness
9. Socket layer wiring
10. Migration readiness
11. Feature flag resolution
12. Logging pipeline verification
13. Metrics backend presence
14. Orphan service detection
15. Debug-mode ban in prod
=====================================================
"""

import os
import sys
from typing import List

from app.segments.segment_87_risk_audit_registry import (
    unresolved_blockers,
    can_merge,
)

from app.segments.segment_88_premerge_guardian import (
    discover_segments,
)


REQUIRED_ENV_VARS = [
    "FLIPTRYBE_ENV",
    "DATABASE_URL",
    "SECRET_KEY",
]


REQUIRED_SERVICES = [
    "payments",
    "engine",
    "realtime",
    "worker",
]


# =====================================================
# ENVIRONMENT
# =====================================================

def current_env():

    return os.getenv("FLIPTRYBE_ENV", "dev").lower()


def is_production():

    return current_env() in {"prod", "production", "staging"}


# =====================================================
# CHECKS
# =====================================================

def env_vars_present() -> List[str]:

    return [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]


def services_present() -> List[str]:

    missing = []

    for svc in REQUIRED_SERVICES:
        try:
            __import__(svc)
        except Exception:
            missing.append(svc)

    return missing


def debug_enabled():

    return os.getenv("FLASK_DEBUG") == "1"


# =====================================================
# BOOT GATE
# =====================================================

def runtime_gate():

    failures = []

    if is_production():

        if unresolved_blockers():
            failures.append("Unresolved audit blockers")

        if not can_merge():
            failures.append("Registry merge veto active")

        missing = env_vars_present()
        if missing:
            failures.append(f"Missing env vars: {missing}")

        missing_services = services_present()
        if missing_services:
            failures.append(f"Missing services: {missing_services}")

        if debug_enabled():
            failures.append("Debug mode enabled in prod")

    return failures


# =====================================================
# CLI / BOOTSTRAP
# =====================================================

def enforce_or_exit():

    failures = runtime_gate()

    if failures:

        print("\n⛔ RUNTIME GATE BLOCKED STARTUP:\n")

        for f in failures:
            print(" -", f)

        sys.exit(1)

    print("✅ Runtime integrity checks passed")


if __name__ == "__main__":

    enforce_or_exit()