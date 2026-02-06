"""
=====================================================
FLIPTRYBE SEGMENT 38
MEGA GENESIS EXTRACTOR & FINAL BUILDER
=====================================================
Run once to materialize final workspace.
=====================================================
"""

import os
from pathlib import Path
import subprocess
import sys


BASE = Path("fliptrybe")
BASE.mkdir(exist_ok=True)


# =====================================================
# DIRECTORY TREE
# =====================================================

DIRS = [
    "app",
    "app/admin",
    "app/marketplace",
    "app/delivery",
    "app/realtime",
    "app/payments",
    "app/risk",
    "app/workers",
    "app/feed",
    "app/moderation",
    "app/signals",
    "app/shortlets",
    "app/search",
    "app/kyc",
    "app/observability",
    "app/merchant",
    "migrations",
    "instance",
]


for d in DIRS:
    (BASE / d).mkdir(parents=True, exist_ok=True)


# =====================================================
# STUB INIT FILES
# =====================================================

for d in DIRS:
    init = BASE / d / "__init__.py"
    if "app" in d and not init.exists():
        init.write_text("")


# =====================================================
# REQUIREMENTS LOCK
# =====================================================

(BASE / "requirements.txt").write_text(
    """
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
Flask-Login==0.6.3
Flask-SocketIO==5.3.6
eventlet==0.35.2
APScheduler==3.10.4
psycopg2-binary
redis
requests
python-dotenv
"""
)


# =====================================================
# PROCFILE
# =====================================================

(BASE / "Procfile").write_text(
    "web: python run.py\n"
)


# =====================================================
# RENDER YAML
# =====================================================

(BASE / "render.yaml").write_text(
    """
services:
- type: web
  name: fliptrybe
  env: python
  buildCommand: pip install -r requirements.txt
  startCommand: python run.py
"""
)


# =====================================================
# SMOKE TEST
# =====================================================

def smoke():

    print("🧪 Running smoke test...")

    try:
        import flask
        import flask_sqlalchemy
        import flask_socketio
        print("✅ Core deps present")
    except Exception as e:
        print("❌ Dependency failure:", e)


if __name__ == "__main__":

    smoke()

    print("🏗️ FlipTrybe Mega Builder complete")