"""
=====================================================
FLIPTRYBE SEGMENT 39
MEGA MERGE ENGINE & BOOT VALIDATOR
=====================================================
Consumes all segment builder files and materializes
final FlipTrybe production workspace.
=====================================================
"""

import sys
import subprocess
from pathlib import Path
import importlib.util


ROOT = Path.cwd()
SEGMENTS_DIR = ROOT / "segments"
FINAL_DIR = ROOT / "fliptrybe"


# =====================================================
# LOAD SEGMENT BUILDERS
# =====================================================

def run_segment(path: Path):

    print(f"🔗 Running segment: {path.name}")

    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


def run_all_segments():

    if not SEGMENTS_DIR.exists():
        print("⚠️ No segments directory found, skipping merge")
        return

    for seg in sorted(SEGMENTS_DIR.glob("segment_*.py")):
        run_segment(seg)


# =====================================================
# IMPORT SANITY SCAN
# =====================================================

def scan_imports():

    print("🔍 Scanning imports...")

    errors = []

    for py in FINAL_DIR.rglob("*.py"):

        try:
            compile(py.read_text(), py.name, "exec")
        except Exception as e:
            errors.append((py, str(e)))

    if errors:
        print("❌ Import scan failed:")
        for p, e in errors:
            print("  ", p, e)
        sys.exit(1)

    print("✅ Import syntax clean")


# =====================================================
# BOOT TEST
# =====================================================

def boot_test():

    print("🚀 Boot validation...")

    sys.path.insert(0, str(FINAL_DIR))

    try:
        from run import app
        print("✅ Flask app loaded")

    except Exception as e:
        print("❌ Flask failed:", e)
        sys.exit(1)


# =====================================================
# DATABASE CHECK
# =====================================================

def db_test():

    try:
        from app import create_app
        from app.extensions import db

        app = create_app()
        with app.app_context():
            db.engine.connect()
            print("✅ Database reachable")

    except Exception as e:
        print("❌ DB failure:", e)
        sys.exit(1)


# =====================================================
# SOCKETIO CHECK
# =====================================================

def socket_test():

    try:
        from run import socketio
        print("✅ SocketIO bound")

    except Exception as e:
        print("❌ SocketIO failure:", e)
        sys.exit(1)


# =====================================================
# MASTER RUN
# =====================================================

if __name__ == "__main__":

    print("🧬 Starting FlipTrybe Mega Merge...")

    run_all_segments()
    scan_imports()
    boot_test()
    db_test()
    socket_test()

    print("------------------------------------------------")
    print("🎉 MERGE SUCCESSFUL. SYSTEM IS COHERENT.")
    print("------------------------------------------------")