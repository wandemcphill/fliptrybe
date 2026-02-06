from __future__ import annotations

import hmac
import hashlib
from datetime import datetime

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import Wallet, Transaction, User
from app.utils.commission import compute_commission, RATES
from app.utils.receipts import create_receipt
from app.utils.notify import queue_in_app, queue_sms, queue_whatsapp, mark_sent

webhooks_bp = Blueprint("webhooks_bp", __name__, url_prefix="/api/webhooks")

_WEBHOOKS_INIT_DONE = False


@webhooks_bp.before_app_request
def _ensure_tables_once():
    global _WEBHOOKS_INIT_DONE
    if _WEBHOOKS_INIT_DONE:
        return
    try:
        db.create_all()
    except Exception:
        pass
    _WEBHOOKS_INIT_DONE = True


def _get_or_create_wallet(user_id: int) -> Wallet:
    w = Wallet.query.filter_by(user_id=user_id).first()
    if w:
        return w
    w = Wallet(user_id=user_id, balance=0.0)
    db.session.add(w)
    db.session.commit()
    return w


def _tx(wallet_id: int, *, amount: float, gross: float, net: float, commission: float, purpose: str, direction: str, reference: str) -> Transaction:
    tx = Transaction(
        wallet_id=wallet_id,
        amount=amount,
        gross_amount=gross,
        net_amount=net,
        commission_total=commission,
        purpose=purpose,
        direction=direction,
        reference=reference[:50],
        created_at=datetime.utcnow(),
    )
    db.session.add(tx)
    return tx


def _verify_paystack(signature: str | None, payload_bytes: bytes, secret: str) -> bool:
    if not signature:
        return False
    try:
        computed = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha512).hexdigest()
        return hmac.compare_digest(computed, signature)
    except Exception:
        return False


@webhooks_bp.post("/paystack")
def paystack_webhook():
    """Stub: validates signature if PAYSTACK_SECRET is set, then credits wallet based on metadata.user_id."""
    secret = (request.environ.get("PAYSTACK_SECRET") or request.headers.get("X-Paystack-Secret") or "").strip()
    sig = request.headers.get("X-Paystack-Signature")

    raw = request.get_data() or b"{}"
    if secret and not _verify_paystack(sig, raw, secret):
        return jsonify({"message": "Invalid signature"}), 400

    payload = request.get_json(silent=True) or {}
    data = payload.get("data") or {}
    meta = (data.get("metadata") or {}) if isinstance(data, dict) else {}
    user_id = meta.get("user_id")

    try:
        uid = int(user_id)
    except Exception:
        return jsonify({"ok": True, "ignored": True}), 200

    amount_kobo = data.get("amount") or 0
    try:
        gross = float(amount_kobo) / 100.0
    except Exception:
        gross = 0.0

    if gross <= 0:
        return jsonify({"ok": True, "ignored": True}), 200

    w = _get_or_create_wallet(uid)
    w.balance = float(w.balance or 0.0) + gross
    _tx(w.id, amount=gross, gross=gross, net=gross, commission=0.0, purpose="topup", direction="credit", reference=f"paystack:{datetime.utcnow().isoformat()}")

    rec = create_receipt(
        user_id=uid,
        kind="topup",
        reference=f"paystack:{datetime.utcnow().isoformat()}",
        amount=gross,
        fee=0.0,
        total=gross,
        description="Wallet topup receipt (webhook)",
        meta={"provider": "paystack"},
    )

    n1 = queue_in_app(uid, "Wallet funded", f"Top up ₦{gross} received.", meta={"receipt_id": None})
    n2 = queue_sms(uid, "Wallet funded", f"FlipTrybe: Top up ₦{gross} received.", provider="stub")
    n3 = queue_whatsapp(uid, "Wallet funded", f"FlipTrybe: Top up ₦{gross} received.", provider="stub")
    mark_sent(n1, "stub:webhook")
    mark_sent(n2, "stub:webhook")
    mark_sent(n3, "stub:webhook")

    try:
        db.session.commit()
        return jsonify({"ok": True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Webhook error", "error": str(e)}), 500


@webhooks_bp.post("/stripe")
def stripe_webhook():
    """Stub: no signature validation here yet. Expects event.data.object.metadata.user_id and amount_total."""
    payload = request.get_json(silent=True) or {}
    data = (((payload.get("data") or {}).get("object") or {}) if isinstance(payload.get("data"), dict) else {})
    meta = (data.get("metadata") or {}) if isinstance(data, dict) else {}
    user_id = meta.get("user_id")

    try:
        uid = int(user_id)
    except Exception:
        return jsonify({"ok": True, "ignored": True}), 200

    amount = data.get("amount_total") or data.get("amount") or 0
    try:
        gross = float(amount) / 100.0
    except Exception:
        gross = 0.0

    if gross <= 0:
        return jsonify({"ok": True, "ignored": True}), 200

    w = _get_or_create_wallet(uid)
    w.balance = float(w.balance or 0.0) + gross
    _tx(w.id, amount=gross, gross=gross, net=gross, commission=0.0, purpose="topup", direction="credit", reference=f"stripe:{datetime.utcnow().isoformat()}")

    rec = create_receipt(
        user_id=uid,
        kind="topup",
        reference=f"stripe:{datetime.utcnow().isoformat()}",
        amount=gross,
        fee=0.0,
        total=gross,
        description="Wallet topup receipt (webhook)",
        meta={"provider": "stripe"},
    )

    n1 = queue_in_app(uid, "Wallet funded", f"Top up ₦{gross} received.", meta={"receipt_id": None})
    n2 = queue_sms(uid, "Wallet funded", f"FlipTrybe: Top up ₦{gross} received.", provider="stub")
    n3 = queue_whatsapp(uid, "Wallet funded", f"FlipTrybe: Top up ₦{gross} received.", provider="stub")
    mark_sent(n1, "stub:webhook")
    mark_sent(n2, "stub:webhook")
    mark_sent(n3, "stub:webhook")

    try:
        db.session.commit()
        return jsonify({"ok": True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Webhook error", "error": str(e)}), 500
