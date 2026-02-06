"""Compatibility wrappers for payment actions.

Some segments expect a `app.payments.service` module.
We re-export the escrow helpers from the payments engine segment.
"""

from __future__ import annotations

from app.segments.segment_payments_engine import (
    hold_escrow,
    escrow_hold,
    release_escrow,
)

__all__ = [
    "hold_escrow",
    "escrow_hold",
    "release_escrow",
]
