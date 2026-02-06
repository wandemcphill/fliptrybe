"""
=====================================================
FLIPTRYBE SEGMENT 42
BLUE / GREEN DEPLOYMENT ORCHESTRATOR
=====================================================
Controls Render-style staged releases with
traffic shifting and automatic rollback
based on Segment 41 smoke tests.
=====================================================
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path

ROOT = Path.cwd()
FINAL_DIR = ROOT / "fliptrybe"

DEPLOY_STATE = ROOT / ".deploy_state.json"
ROLLBACK_FLAG = ROOT / ".rollback_ready"
VERSION_FILE = FINAL_DIR / "VERSION"


# =====================================================
# UTILS
# =====================================================

def log(msg):
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{stamp}] {msg}")


def save_state(state):
    DEPLOY_STATE.write_text(json.dumps(state, indent=2))


def load_state():
    if DEPLOY_STATE.exists():
        return json.loads(DEPLOY_STATE.read_text())
    return {}


# =====================================================
# VERSIONING
# =====================================================

def stamp_version():

    version = time.strftime("%Y.%m.%d.%H%M")
    VERSION_FILE.write_text(version)
    log(f"🏷️ Version stamped: {version}")
    return version


# =====================================================
# ENVIRONMENTS
# =====================================================

def start_stack(color):

    log(f"🚀 Starting {color.upper()} stack")

    env = os.environ.copy()
    env["DEPLOY_COLOR"] = color

    return subprocess.Popen(
        [sys.executable, "run.py"],
        cwd=FINAL_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def stop_stack(proc, color):

    log(f"🛑 Stopping {color.upper()} stack")
    proc.terminate()
    proc.wait(timeout=15)


# =====================================================
# TRAFFIC SWITCH
# =====================================================

def switch_traffic(color):

    log(f"🌐 Switching traffic to {color.upper()}")

    marker = ROOT / ".active_color"
    marker.write_text(color)


# =====================================================
# HEALTH GATE
# =====================================================

def smoke_test():

    log("🧪 Running Segment 41 smoke tests")

    res = subprocess.call(
        [sys.executable, "segment_41_smoke_tests.py"],
        cwd=ROOT,
    )

    return res == 0


# =====================================================
# MASTER
# =====================================================

if __name__ == "__main__":

    log("============================================")
    log("SEGMENT 42 DEPLOY CONTROLLER")
    log("============================================")

    current = load_state().get("active", "blue")
    next_color = "green" if current == "blue" else "blue"

    version = stamp_version()

    log(f"♻️ Current: {current.upper()}  Next: {next_color.upper()}")

    proc = start_stack(next_color)

    time.sleep(8)

    if not smoke_test():

        log("🔥 Smoke tests failed")
        stop_stack(proc, next_color)
        sys.exit(1)

    switch_traffic(next_color)

    state = {
        "active": next_color,
        "previous": current,
        "version": version,
        "timestamp": time.time(),
    }

    save_state(state)

    log("🎯 Traffic promoted")

    time.sleep(3)

    # Shutdown old stack
    old_proc = start_stack(current)
    stop_stack(old_proc, current)

    log("✅ Blue-Green rotation complete")