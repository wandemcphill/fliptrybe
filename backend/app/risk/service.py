"""Risk scanning utilities (stub).

Some payment-related segments import this module. In early builds we keep it
as a safe no-op so the app can start even when a full risk engine isn't yet
implemented.
"""

from __future__ import annotations

from typing import Any

def run_risk_scan(*args: Any, **kwargs: Any) -> float:
    """Run a risk scan (placeholder).

    IMPORTANT: Callers compare this as a numeric score (0.0 - 1.0).
    Returning a float avoids startup/runtime crashes when segments do:
        if run_risk_scan(order) > 0.8: ...

    Until a real risk engine exists, we default to "low risk".
    """

    # keep arguments to make future implementation drop-in
    _ = args, kwargs
    return 0.0
