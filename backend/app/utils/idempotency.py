from __future__ import annotations

import hashlib
import json
from typing import Any

from flask import request

from app.extensions import db
from app.models import IdempotencyKey


def _hash_request(payload: Any) -> str:
    try:
        raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    except Exception:
        raw = str(payload).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def get_idempotency_key() -> str | None:
    # Common header pattern
    k = request.headers.get("Idempotency-Key") or request.headers.get("X-Idempotency-Key")
    if not k:
        return None
    return k.strip()[:128]


def lookup_response(user_id: int | None, route: str, payload: Any):
    k = get_idempotency_key()
    if not k:
        return None

    rh = _hash_request(payload)
    row = IdempotencyKey.query.filter_by(key=k).first()
    if row:
        # If same key but different payload, treat as conflict
        if row.request_hash and row.request_hash != rh:
            return ("conflict", {"ok": False, "message": "Idempotency key reuse with different payload"}, 409)
        if row.response_json:
            try:
                return ("hit", json.loads(row.response_json), int(row.status_code or 200))
            except Exception:
                return ("hit", {"ok": True}, int(row.status_code or 200))
        return ("hit", {"ok": True}, int(row.status_code or 200))

    row = IdempotencyKey(key=k, user_id=int(user_id) if user_id is not None else None, route=route, request_hash=rh)
    db.session.add(row)
    db.session.commit()
    return ("miss", row, 0)


def store_response(row: IdempotencyKey, response_json: Any, status_code: int):
    try:
        row.response_json = json.dumps(response_json, default=str)
    except Exception:
        row.response_json = json.dumps({"ok": True})
    row.status_code = int(status_code)
    db.session.add(row)
    db.session.commit()
