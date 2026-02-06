"""
=====================================================
FLIPTRYBE SEGMENT 36
RENDER DEPLOYMENT & PROD BOOTSTRAP
=====================================================
Do not merge yet.
"""

import os
import sys

from flask import current_app

from app import create_app
from app.extensions import socketio

from app.segments.segment_background_jobs import start_scheduler


# =====================================================
# ENV VALIDATION
# =====================================================

REQUIRED_ENV = [
    "SECRET_KEY",
    "DATABASE_URL",
    "PAYSTACK_SECRET_KEY",
    "TERMII_API_KEY",
]


def validate_env():

    missing = []

    for k in REQUIRED_ENV:
        if not os.getenv(k):
            missing.append(k)

    if missing:
        raise RuntimeError(
            f"Missing env vars: {', '.join(missing)}"
        )


# =====================================================
# BOOTSTRAP
# =====================================================

def boot():

    validate_env()

    app = create_app()

    start_scheduler()

    return app


# =====================================================
# ENTRY
# =====================================================

if __name__ == "__main__":

    app = boot()

    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
    )


print("🚀 Segment 36 Loaded: Render Deployment Ready")