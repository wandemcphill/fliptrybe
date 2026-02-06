from __future__ import annotations

import os
import requests

TERMII_BASE = "https://api.ng.termii.com/api"


def send_termii_message(*, channel: str, to: str, message: str) -> tuple[bool, str]:
    """Send SMS or WhatsApp via Termii.

    Termii uses the same endpoint for SMS and WhatsApp; switch via `channel`.
    - SMS: channel="generic" (or "dnd" if you have it enabled)
    - WhatsApp: channel="whatsapp"
    """

    api_key = os.getenv("TERMII_API_KEY")
    sender = os.getenv("TERMII_SENDER_ID", "FlipTrybe")

    if not api_key:
        return False, "TERMII_API_KEY not set"

    ch = (channel or "generic").strip().lower()
    if ch not in {"generic", "dnd", "whatsapp"}:
        ch = "generic"

    payload = {
        "to": (to or "").strip(),
        "from": sender,
        "sms": message,
        "type": "plain",
        "channel": ch,
        "api_key": api_key,
    }

    try:
        r = requests.post(f"{TERMII_BASE}/sms/send", json=payload, timeout=10)
        if 200 <= r.status_code < 300:
            return True, "sent"
        return False, f"termii_http_{r.status_code}"
    except Exception as e:
        return False, f"termii_exception:{e}"
