from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import User, Order, DriverJobOffer, AuditLog
from app.utils.jwt_utils import decode_token
from app.utils.escrow_unlocks import ensure_unlock, set_code_if_missing
from app.utils.notify import queue_sms, queue_whatsapp

driver_offer_bp = Blueprint("driver_offer_bp", __name__, url_prefix="/api/driver/offers")

_INIT = False


@driver_offer_bp.before_app_request
def _ensure_tables_once():
    global _INIT
    if _INIT:
        return
    try:
        db.create_all()
    except Exception:
        pass
    _INIT = True


def _bearer():
    h = request.headers.get("Authorization", "")
    if not h.startswith("Bearer "):
        return None
    return h.replace("Bearer ", "", 1).strip()


def _current_user():
    tok = _bearer()
    if not tok:
        return None
    payload = decode_token(tok)
    if not payload:
        return None
    sub = payload.get("sub")
    if not sub:
        return None
    try:
        uid = int(sub)
    except Exception:
        return None
    return User.query.get(uid)


@driver_offer_bp.get("")
def my_offers():
    u = _current_user()
    if not u or (u.role or "") != "driver":
        return jsonify([]), 200
    rows = DriverJobOffer.query.filter_by(driver_id=int(u.id)).order_by(DriverJobOffer.created_at.desc()).limit(50).all()
    return jsonify([r.to_dict() for r in rows]), 200


@driver_offer_bp.post("/<int:offer_id>/accept")
def accept(offer_id: int):
    u = _current_user()
    if not u:
        return jsonify({"message": "Unauthorized"}), 401
    if (u.role or "") != "driver":
        return jsonify({"message": "Driver role required"}), 403

    off = DriverJobOffer.query.get(offer_id)
    if not off or int(off.driver_id) != int(u.id):
        return jsonify({"message": "Not found"}), 404
    if off.status != "offered":
        return jsonify({"message": "Offer not active"}), 400

    o = Order.query.get(int(off.order_id))
    if not o:
        return jsonify({"message": "Order not found"}), 404

    off.status = "accepted"
    off.decided_at = datetime.utcnow()
    o.driver_id = int(u.id)
    o.status = "assigned"

    try:
        unlock = ensure_unlock(int(o.id), "pickup_seller")
        code = set_code_if_missing(unlock, int(o.id), "pickup_seller")
        if code:
            msg = f"FlipTrybe: Pickup code for Order #{int(o.id)} is {code}. Keep private."
            queue_sms(int(u.id), "FlipTrybe", msg, meta={"order_id": int(o.id)})
            queue_whatsapp(int(u.id), "FlipTrybe", msg, meta={"order_id": int(o.id)})
        db.session.add(unlock)
    except Exception:
        pass

    db.session.add(off)
    db.session.add(o)
    db.session.commit()

    try:
        db.session.add(AuditLog(actor_user_id=int(u.id), action="driver_accept", target_type="order", target_id=int(o.id), meta=f"offer={off.id}"))
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify({"ok": True, "offer": off.to_dict()}), 200


@driver_offer_bp.post("/<int:offer_id>/reject")
def reject(offer_id: int):
    u = _current_user()
    if not u:
        return jsonify({"message": "Unauthorized"}), 401
    if (u.role or "") != "driver":
        return jsonify({"message": "Driver role required"}), 403

    off = DriverJobOffer.query.get(offer_id)
    if not off or int(off.driver_id) != int(u.id):
        return jsonify({"message": "Not found"}), 404
    if off.status != "offered":
        return jsonify({"message": "Offer not active"}), 400

    off.status = "rejected"
    off.decided_at = datetime.utcnow()
    db.session.add(off)
    db.session.commit()

    try:
        db.session.add(AuditLog(actor_user_id=int(u.id), action="driver_reject", target_type="order", target_id=int(off.order_id), meta=f"offer={off.id}"))
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify({"ok": True, "offer": off.to_dict()}), 200
