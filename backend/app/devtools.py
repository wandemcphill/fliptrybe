
import os
from flask import Blueprint, jsonify, current_app
from app.extensions import db
from app.models import User
from werkzeug.security import generate_password_hash

dev = Blueprint("devtools", __name__, url_prefix="/dev")

REQUIRED_ENV_VARS = [
    "SECRET_KEY",
    "DATABASE_URL",
]

OPTIONAL_BUT_COMMON = [
    "PAYSTACK_SECRET_KEY",
    "TERMII_API_KEY",
    "TERMII_SENDER_ID",
    "REDIS_URL",
    "ADMIN_EMAIL",
    "ADMIN_PASSWORD",
]

@dev.get("/routes")
def list_routes():
    # Lists all registered routes. Helpful to verify "buttons" endpoints exist in prod.
    out = []
    for rule in sorted(current_app.url_map.iter_rules(), key=lambda r: r.rule):
        methods = sorted([m for m in rule.methods if m not in ("HEAD", "OPTIONS")])
        out.append({"rule": rule.rule, "methods": methods, "endpoint": rule.endpoint})
    return jsonify(out)

@dev.get("/env")
def env_check():
    missing_required = [k for k in REQUIRED_ENV_VARS if not os.getenv(k)]
    present_optional = [k for k in OPTIONAL_BUT_COMMON if os.getenv(k)]
    missing_optional = [k for k in OPTIONAL_BUT_COMMON if not os.getenv(k)]
    return jsonify({
        "missing_required": missing_required,
        "present_optional": present_optional,
        "missing_optional": missing_optional,
        "note": "Set missing_required in Render Environment. Optional vars depend on which features you use."
    })

@dev.post("/seed-admin")
def seed_admin():
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")
    if not email or not password:
        return jsonify({"error": "Set ADMIN_EMAIL and ADMIN_PASSWORD env vars first."}), 400
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({"ok": True, "message": "Admin already exists", "user_id": user.id})
    user = User(email=email, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    return jsonify({"ok": True, "message": "Admin created", "user_id": user.id})


@dev.post("/db/create-all")
def db_create_all():
    """Dev helper: create all tables from models (no migrations required).
    Useful for quick local testing. DO NOT use as a production migration strategy.
    """
    db.create_all()
    return jsonify({"ok": True, "message": "db.create_all() executed"})

@dev.get("/db/info")
def db_info():
    """Basic DB info + table list."""
    try:
        insp = db.inspect(db.engine)
        tables = sorted(insp.get_table_names())
        return jsonify({"ok": True, "tables": tables, "count": len(tables)})
    except Exception as e:
        return jsonify({"ok": False, "error": f"{type(e).__name__}: {e}"}), 500
