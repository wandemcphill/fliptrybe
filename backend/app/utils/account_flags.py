from __future__ import annotations

import json

from app.extensions import db
from app.models import AccountFlag, DriverProfile, MerchantProfile, InspectorProfile, PayoutRequest


def _safe_json(details: dict | None) -> str | None:
    if details is None:
        return None
    try:
        return json.dumps(details, default=str)
    except Exception:
        try:
            return str(details)
        except Exception:
            return None


def record_account_flag(user_id: int, flag_type: str, signal: str = "", details: dict | None = None) -> None:
    if not user_id:
        return
    try:
        flag = AccountFlag(
            user_id=int(user_id),
            flag_type=(flag_type or "").strip() or "UNKNOWN",
            signal=(signal or "").strip() or None,
            details=_safe_json(details),
        )
        db.session.add(flag)
        db.session.commit()
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass


def find_duplicate_phone_users(user_id: int, phone: str) -> list[int]:
    p = (phone or "").strip()
    if not p:
        return []
    other_user_ids: set[int] = set()
    try:
        rows = DriverProfile.query.filter(DriverProfile.phone == p).all()
        for r in rows:
            if int(r.user_id) != int(user_id):
                other_user_ids.add(int(r.user_id))
    except Exception:
        pass
    try:
        rows = MerchantProfile.query.filter(MerchantProfile.phone == p).all()
        for r in rows:
            if int(r.user_id) != int(user_id):
                other_user_ids.add(int(r.user_id))
    except Exception:
        pass
    try:
        rows = InspectorProfile.query.filter(InspectorProfile.phone == p).all()
        for r in rows:
            if int(r.user_id) != int(user_id):
                other_user_ids.add(int(r.user_id))
    except Exception:
        pass
    if not other_user_ids:
        return []
    return sorted(list(other_user_ids))


def flag_duplicate_phone(user_id: int, phone: str) -> list[int]:
    other_user_ids = find_duplicate_phone_users(user_id, phone)
    if not other_user_ids:
        return []
    p = (phone or "").strip()
    for other_id in other_user_ids:
        record_account_flag(
            other_id,
            "DUP_PHONE",
            signal=p,
            details={"phone": p, "other_user_id": int(user_id)},
        )
    record_account_flag(
        int(user_id),
        "DUP_PHONE",
        signal=p,
        details={"phone": p, "other_user_ids": other_user_ids},
    )
    return other_user_ids


def find_duplicate_bank_users(user_id: int, account_number: str) -> list[int]:
    acct = (account_number or "").strip()
    if not acct:
        return []
    other_user_ids: set[int] = set()
    try:
        rows = (
            PayoutRequest.query
            .filter(PayoutRequest.account_number == acct)
            .filter(PayoutRequest.user_id != int(user_id))
            .all()
        )
        for r in rows:
            other_user_ids.add(int(r.user_id))
    except Exception:
        pass
    if not other_user_ids:
        return []
    return sorted(list(other_user_ids))


def flag_duplicate_bank(user_id: int, account_number: str, bank_name: str = "", account_name: str = "") -> list[int]:
    acct = (account_number or "").strip()
    other_user_ids = find_duplicate_bank_users(user_id, acct)
    if not other_user_ids:
        return []
    details = {"account_number": acct, "bank_name": bank_name or "", "account_name": account_name or ""}
    for other_id in other_user_ids:
        record_account_flag(
            other_id,
            "DUP_BANK",
            signal=acct,
            details={**details, "other_user_id": int(user_id)},
        )
    record_account_flag(
        int(user_id),
        "DUP_BANK",
        signal=acct,
        details={**details, "other_user_ids": other_user_ids},
    )
    return other_user_ids
