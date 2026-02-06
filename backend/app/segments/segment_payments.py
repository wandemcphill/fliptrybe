from __future__ import annotations

import json
import os
from datetime import datetime

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import AuditLog, User, PaymentIntent, WebhookEvent
from app.utils.jwt_utils import decode_token
from app.utils.paystack_client import initialize_transaction, verify_signature
from app.utils.wallets import post_txn
from app.utils.idempotency import lookup_response, store_response

payments_bp = Blueprint("payments_bp", __name__, url_prefix="/api/payments")

_INIT = False


@payments_bp.before_app_request
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


@payments_bp.post("/initialize")
def initialize_payment():
    u = _current_user()
    if not u:
        return jsonify({"message": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}

    idem = lookup_response(int(u.id), '/api/payments/initialize', data)
    if idem and idem[0] == 'hit':
        return jsonify(idem[1]), idem[2]
    if idem and idem[0] == 'conflict':
        return jsonify(idem[1]), idem[2]
    idem_row = idem[1] if idem and idem[0] == 'miss' else None
    amount = float(data.get("amount") or 0.0)
    purpose = (data.get("purpose") or "topup").strip()
    if amount <= 0:
        return jsonify({"message": "amount must be > 0"}), 400

    ref = f"FT-{int(u.id)}-{int(datetime.utcnow().timestamp())}"

    pi = PaymentIntent(user_id=int(u.id), provider="paystack", reference=ref, purpose=purpose, amount=float(amount), status="initialized")
    db.session.add(pi)
    db.session.commit()

    try:
        db.session.add(AuditLog(actor_user_id=int(u.id), action="payment_init", target_type="payment_intent", target_id=int(pi.id), meta=json.dumps({"amount": amount, "purpose": purpose, "ref": ref})))
        db.session.commit()
    except Exception:
        db.session.rollback()

    init = initialize_transaction(email=u.email, amount_ngn=float(amount), reference=ref)
    if not init.get("ok"):
        resp = {"ok": True, "provider": "SIM", "reference": ref, "authorization_url": "https://example.com/pay"}
        if idem_row is not None:
            store_response(idem_row, resp, 200)
        return jsonify(resp), 200

    resp = {"ok": True, "provider": "paystack", "reference": ref, "authorization_url": init.get("authorization_url", "")}
    if idem_row is not None:
        store_response(idem_row, resp, 200)
    return jsonify(resp), 200


def _credit_wallet_from_reference(reference: str):
    pi = PaymentIntent.query.filter_by(reference=reference).first()
    if not pi:
        return False
    if pi.status == "paid":
        return True

    pi.status = "paid"
    pi.paid_at = datetime.utcnow()
    db.session.add(pi)
    db.session.commit()

    post_txn(int(pi.user_id), float(pi.amount or 0.0), kind="topup", direction="credit", reference=f"pay:{reference}")
    return True


@payments_bp.post("/webhook/paystack")
def paystack_webhook():
    raw = request.get_data() or b""
    sig = request.headers.get("X-Paystack-Signature")
    verified = verify_signature(raw, sig) if sig else False
    strict = os.getenv('PAYSTACK_WEBHOOK_STRICT', '0').strip() == '1'
    if strict and not verified:
        return jsonify({'ok': False, 'message': 'Invalid signature'}), 401

    payload = request.get_json(silent=True) or {}
    try:
        db.session.add(AuditLog(actor_user_id=None, action="paystack_webhook", target_type="webhook", target_id=None, meta=json.dumps({"verified": verified, "payload": payload})))
        db.session.commit()
    except Exception:
        db.session.rollback()

    event = (payload.get("event") or "").strip()
    data = payload.get("data") or {}
    reference = (data.get("reference") or "").strip()

    # Replay protection: derive event_id and ignore duplicates
    event_id = ""
    try:
        event_id = (payload.get("id") or payload.get("event_id") or "").strip()
    except Exception:
        event_id = ""
    if not event_id:
        # Fallback deterministic id based on event+reference+amount
        try:
            import hashlib
            base = f"{event}:{reference}:{data.get('amount','')}"
            event_id = hashlib.sha256(base.encode("utf-8")).hexdigest()[:32]
        except Exception:
            event_id = f"evt_{reference}"

    existing = WebhookEvent.query.filter_by(provider="paystack", event_id=event_id).first()
    if existing:
        return jsonify({"ok": True, "replayed": True, "verified": verified}), 200

    try:
        db.session.add(WebhookEvent(provider="paystack", event_id=event_id, reference=reference))
        db.session.commit()
    except Exception:
        db.session.rollback()


    if event == "charge.success" and reference:
        _credit_wallet_from_reference(reference)

    return jsonify({"ok": True, "verified": verified}), 200
