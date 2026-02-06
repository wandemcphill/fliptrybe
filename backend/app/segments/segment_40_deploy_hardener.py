"""
=====================================================
FLIPTRYBE SEGMENT 40
DEPLOYMENT HARDENER & RELEASE PREPARER
=====================================================
Validates env vars, generates migrations, seeds
admin user, snapshots production build.
=====================================================
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


ROOT = Path.cwd()
FINAL_DIR = ROOT / "fliptrybe"
INSTANCE_DIR = FINAL_DIR / "instance"
SNAPSHOT_DIR = ROOT / "release_snapshot"


REQUIRED_ENV = [
    "SECRET_KEY",
    "DATABASE_URL",
    "PAYSTACK_SECRET_KEY",
    "PAYSTACK_PUBLIC_KEY",
]


# =====================================================
# ENV VALIDATOR
# =====================================================

def validate_env():

    print("🔐 Validating environment variables...")

    missing = [k for k in REQUIRED_ENV if not os.getenv(k)]

    if missing:
        print("❌ Missing required environment variables:")
        for k in missing:
            print("   ", k)
        sys.exit(1)

    print("✅ Environment OK")


# =====================================================
# MIGRATION AUTOGEN
# =====================================================

def run_migrations():

    print("📜 Generating migrations...")

    env = os.environ.copy()
    env["FLASK_APP"] = "run.py"

    subprocess.run(
        ["flask", "db", "init"],
        cwd=FINAL_DIR,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    subprocess.check_call(
        ["flask", "db", "migrate", "-m", "Genesis auto migration"],
        cwd=FINAL_DIR,
        env=env,
    )

    subprocess.check_call(
        ["flask", "db", "upgrade"],
        cwd=FINAL_DIR,
        env=env,
    )

    print("✅ Migrations complete")


# =====================================================
# ADMIN SEEDER
# =====================================================

def seed_admin():

    print("👑 Seeding admin user...")

    sys.path.insert(0, str(FINAL_DIR))

    from app import create_app
    from app.extensions import db
    from app.models import User

    app = create_app()

    with app.app_context():

        email = os.getenv("ADMIN_EMAIL", "admin@fliptrybe.com")
        password = os.getenv("ADMIN_PASSWORD", "ChangeMe123!")

        admin = User.query.filter_by(email=email).first()

        if not admin:

            admin = User(
                name="Super Admin",
                email=email,
                phone="0000000000",
                is_admin=True,
                is_verified=True,
            )
            admin.set_password(password)

            db.session.add(admin)
            db.session.commit()

            print(f"✅ Admin created: {email}")

        else:
            print("ℹ️ Admin already exists")


# =====================================================
# SNAPSHOT BUILDER
# =====================================================

def snapshot_release():

    print("📦 Creating release snapshot...")

    if SNAPSHOT_DIR.exists():
        shutil.rmtree(SNAPSHOT_DIR)

    shutil.copytree(FINAL_DIR, SNAPSHOT_DIR)

    print(f"✅ Snapshot saved to {SNAPSHOT_DIR}")


# =====================================================
# MASTER
# =====================================================

if __name__ == "__main__":

    print("🚀 Segment 40 starting...")

    validate_env()
    run_migrations()
    seed_admin()
    snapshot_release()

    print("------------------------------------------------")
    print("🎉 SEGMENT 40 COMPLETE: DEPLOYMENT READY")
    print("------------------------------------------------")