from __future__ import annotations

from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import User, WalletTxn

leader_bp = Blueprint("leader_bp", __name__, url_prefix="/api/leaderboard")

_INIT = False


@leader_bp.before_app_request
def _ensure_tables_once():
    global _INIT
    if _INIT:
        return
    try:
        db.create_all()
    except Exception:
        pass
    _INIT = True


@leader_bp.get("/merchants")
def top_merchants():
    days = int(request.args.get("days") or 30)
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.session.query(WalletTxn.user_id, db.func.sum(WalletTxn.amount).label("earnings"))
        .filter(WalletTxn.kind == "order_sale", WalletTxn.direction == "credit", WalletTxn.created_at >= since)
        .group_by(WalletTxn.user_id)
        .order_by(db.desc("earnings"))
        .limit(50)
        .all()
    )
    out = []
    for uid, earnings in rows:
        u = User.query.get(int(uid))
        if not u:
            continue
        out.append({"user_id": int(uid), "name": u.name, "role": u.role or "buyer", "earnings": float(earnings or 0.0)})
    return jsonify(out), 200


@leader_bp.get("/drivers")
def top_drivers():
    days = int(request.args.get("days") or 30)
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.session.query(WalletTxn.user_id, db.func.sum(WalletTxn.amount).label("earnings"))
        .filter(WalletTxn.kind == "delivery_fee", WalletTxn.direction == "credit", WalletTxn.created_at >= since)
        .group_by(WalletTxn.user_id)
        .order_by(db.desc("earnings"))
        .limit(50)
        .all()
    )
    out = []
    for uid, earnings in rows:
        u = User.query.get(int(uid))
        if not u:
            continue
        out.append({"user_id": int(uid), "name": u.name, "role": u.role or "buyer", "earnings": float(earnings or 0.0)})
    return jsonify(out), 200
