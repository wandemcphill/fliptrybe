from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Dict, Optional

from app.extensions import db
from app.models.receipt import Receipt


def create_receipt(
    *,
    user_id: int,
    kind: str,
    reference: str,
    amount: float,
    fee: float,
    total: float,
    description: str = "",
    meta: Optional[Dict[str, Any]] = None,
) -> Receipt:
    r = Receipt(
        user_id=user_id,
        kind=(kind or "")[:40],
        reference=(reference or "")[:120],
        amount=float(amount or 0.0),
        fee=float(fee or 0.0),
        total=float(total or 0.0),
        description=description or "",
        created_at=datetime.utcnow(),
        meta=json.dumps(meta or {}),
    )
    db.session.add(r)
    return r
