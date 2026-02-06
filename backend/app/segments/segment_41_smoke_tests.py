"""
=====================================================
FLIPTRYBE SEGMENT 41
PRODUCTION SMOKE TEST & ROLLBACK GUARD
=====================================================
Boots app in prod mode, validates core services,
Socket.IO, DB connectivity, blueprints, Redis,
and produces rollback markers.
=====================================================
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

ROOT = Path.cwd()
FINAL_DIR = ROOT / "fliptrybe"
LOG_DIR = ROOT / "deploy_logs"
ROLLBACK_FLAG = ROOT / ".rollback_ready"


LOG_DIR.mkdir(exist_ok=True)


# =====================================================
# LOGGER
# =====================================================

def log(msg):
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line)
    with open(LOG_DIR / "segment_41.log", "a") as f:
        f.write(line + "\n")


# =====================================================
# BOOTSTRAP APP
# =====================================================

def boot_app():

    log("🚀 Booting app in production mode")

    env = os.environ.copy()
    env["FLASK_DEBUG"] = "False"

    proc = subprocess.Popen(
        [sys.executable, "run.py"],
        cwd=FINAL_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    time.sleep(6)
    return proc


# =====================================================
# HTTP PROBE
# =====================================================

def http_probe():

    log("🌐 Probing HTTP endpoints")

    import requests

    endpoints = [
        "http://127.0.0.1:5000/api/payments/release/0",
        "http://127.0.0.1:5000/api/realtime/signal",
    ]

    failures = 0

    for url in endpoints:
        try:
            r = requests.get(url, timeout=3)
            log(f"{url} -> {r.status_code}")
        except Exception as e:
            log(f"❌ {url} failed: {e}")
            failures += 1

    return failures == 0


# =====================================================
# SOCKET.IO PROBE
# =====================================================

def socket_probe():

    log("🔌 Probing Socket.IO")

    try:
        import socketio

        sio = socketio.Client()
        sio.connect("http://127.0.0.1:5000", wait_timeout=4)
        sio.disconnect()
        log("✅ Socket.IO OK")
        return True

    except Exception as e:
        log(f"❌ Socket.IO failed: {e}")
        return False


# =====================================================
# REDIS PROBE
# =====================================================

def redis_probe():

    log("📡 Probing Redis")

    try:
        import redis

        r = redis.from_url(os.getenv("REDIS_URL"))
        r.ping()
        log("✅ Redis OK")
        return True

    except Exception as e:
        log(f"⚠️ Redis skipped or failed: {e}")
        return False


# =====================================================
# DB PROBE
# =====================================================

def db_probe():

    log("🗄️ Probing database")

    sys.path.insert(0, str(FINAL_DIR))

    from app import create_app
    from app.extensions import db

    app = create_app()

    with app.app_context():
        db.engine.execute("SELECT 1")

    log("✅ DB OK")
    return True


# =====================================================
# MASTER
# =====================================================

if __name__ == "__main__":

    log("================================================")
    log("SEGMENT 41 START")
    log("================================================")

    proc = boot_app()

    failures = 0

    if not db_probe():
        failures += 1

    if not socket_probe():
        failures += 1

    if not redis_probe():
        failures += 1

    if not http_probe():
        failures += 1

    proc.terminate()

    if failures:

        log("❌ Smoke tests FAILED")
        ROLLBACK_FLAG.write_text("rollback permitted")

        sys.exit(1)

    log("🎉 Smoke tests PASSED")
    ROLLBACK_FLAG.write_text("deploy safe")