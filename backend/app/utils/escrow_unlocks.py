from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Tuple

from flask import current_app

from app.extensions import db
from app.models import EscrowUnlock, QRChallenge


def _now() -> datetime:
    return datetime.utcnow()


def _secret_bytes() -> bytes:
    try:
        secret = current_app.config.get("SECRET_KEY") or ""
    except Exception:
        secret = ""
    if not secret:
        secret = (os.getenv("SECRET_KEY") or "dev-secret")
    return str(secret).encode()


def _hmac_hex(value: str) -> str:
    return hmac.new(_secret_bytes(), value.encode(), hashlib.sha256).hexdigest()


def generate_code() -> str:
    return f"{secrets.randbelow(10000):04d}"


def hash_code(order_id: int, step: str, code: str) -> str:
    raw = f"{int(order_id)}:{step}:{code}"
    return _hmac_hex(raw)


def ensure_unlock(order_id: int, step: str, *, expires_hours: int = 24) -> EscrowUnlock:
    row = EscrowUnlock.query.filter_by(order_id=int(order_id), step=step).first()
    if row:
        return row
    row = EscrowUnlock(
        order_id=int(order_id),
        step=step,
        expires_at=_now() + timedelta(hours=int(expires_hours)) if expires_hours else None,
    )
    db.session.add(row)
    return row


def set_code_if_missing(unlock: EscrowUnlock, order_id: int, step: str, *, expires_hours: int = 24) -> str | None:
    if (unlock.code_hash or "").strip():
        return None
    code = generate_code()
    unlock.code_hash = hash_code(int(order_id), step, code)
    if not unlock.expires_at and expires_hours:
        unlock.expires_at = _now() + timedelta(hours=int(expires_hours))
    db.session.add(unlock)
    return code


def verify_code(unlock: EscrowUnlock, order_id: int, step: str, code: str) -> bool:
    if not (unlock.code_hash or "").strip():
        return False
    return hmac.compare_digest(str(unlock.code_hash), hash_code(int(order_id), step, str(code).strip()))


def bump_attempts(unlock: EscrowUnlock) -> bool:
    try:
        unlock.attempts = int(unlock.attempts or 0) + 1
        if int(unlock.attempts) >= int(unlock.max_attempts or 4):
            unlock.locked = True
            return False
        return True
    except Exception:
        unlock.locked = True
        return False


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64url_decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + padding)


def issue_qr_token(order_id: int, step: str, issued_to_role: str, *, expires_minutes: int = 15) -> str:
    nonce = secrets.token_urlsafe(24)
    payload = {
        "order_id": int(order_id),
        "step": step,
        "issued_to_role": issued_to_role,
        "nonce": nonce,
        "issued_at": int(_now().timestamp()),
    }
    payload_raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    payload_b64 = _b64url_encode(payload_raw)
    sig = _hmac_hex(payload_b64)
    token = f"{payload_b64}.{sig}"

    # Expire previous issued challenges for this order/step.
    try:
        QRChallenge.query.filter_by(order_id=int(order_id), step=step, status="issued").update({"status": "expired"})
    except Exception:
        pass

    challenge_hash = _hmac_hex(f"{int(order_id)}:{step}:{nonce}")
    row = QRChallenge(
        order_id=int(order_id),
        step=step,
        issued_to_role=str(issued_to_role),
        challenge_hash=challenge_hash,
        status="issued",
        issued_at=_now(),
        expires_at=_now() + timedelta(minutes=int(expires_minutes)),
    )
    db.session.add(row)
    return token


def verify_qr_token(token: str, order_id: int, step: str | None = None) -> Tuple[bool, str, Dict[str, Any] | None, QRChallenge | None]:
    if not token or "." not in token:
        return False, "Invalid token", None, None
    payload_b64, sig = token.split(".", 1)
    expected = _hmac_hex(payload_b64)
    if not hmac.compare_digest(str(sig), str(expected)):
        return False, "Invalid signature", None, None

    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except Exception:
        return False, "Invalid payload", None, None

    try:
        if int(payload.get("order_id")) != int(order_id):
            return False, "Order mismatch", None, None
    except Exception:
        return False, "Order mismatch", None, None
    payload_step = (payload.get("step") or "")
    if step:
        if payload_step != step:
            return False, "Step mismatch", None, None
    step = payload_step

    issued_at = payload.get("issued_at") or 0
    try:
        issued_at_dt = datetime.utcfromtimestamp(int(issued_at))
    except Exception:
        return False, "Invalid timestamp", None, None
    if _now() > (issued_at_dt + timedelta(minutes=15)):
        return False, "Token expired", None, None

    nonce = payload.get("nonce") or ""
    if not nonce:
        return False, "Invalid nonce", None, None

    challenge_hash = _hmac_hex(f"{int(order_id)}:{step}:{nonce}")
    row = QRChallenge.query.filter_by(order_id=int(order_id), step=step, challenge_hash=challenge_hash).first()
    if not row:
        return False, "Challenge not found", None, None
    if (row.status or "") != "issued":
        return False, "Challenge already used", None, row
    if row.expires_at and _now() > row.expires_at:
        row.status = "expired"
        db.session.add(row)
        return False, "Challenge expired", None, row

    return True, "ok", payload, row


def mark_qr_scanned(row: QRChallenge, *, scanned_by_user_id: int | None = None) -> None:
    row.status = "scanned"
    row.scanned_at = _now()
    if scanned_by_user_id:
        row.scanned_by_user_id = int(scanned_by_user_id)
    db.session.add(row)


def mark_unlock_qr_verified(order_id: int, step: str) -> EscrowUnlock | None:
    unlock = EscrowUnlock.query.filter_by(order_id=int(order_id), step=step).first()
    if not unlock:
        return None
    unlock.qr_verified = True
    unlock.qr_verified_at = _now()
    db.session.add(unlock)
    return unlock


def generate_admin_unlock_token() -> str:
    return secrets.token_urlsafe(16)


def hash_admin_unlock_token(order_id: int, step: str, token: str) -> str:
    return _hmac_hex(f"admin:{int(order_id)}:{step}:{token}")
