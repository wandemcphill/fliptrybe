"""
=====================================================
FLIPTRYBE SEGMENT 60
OTP ORCHESTRATION ENGINE
=====================================================
Generates delivery OTPs,
sends via SMS/WhatsApp,
enforces retries,
locks orders,
releases escrow.
=====================================================
"""

import secrets
import time
from dataclasses import dataclass, field
from typing import Dict, Optional


# =====================================================
# MODELS
# =====================================================

@dataclass
class OTPRecord:
    order_id: int
    buyer_id: int
    driver_id: int
    code: str
    created_at: float
    expires_at: float
    attempts: int = 0
    locked: bool = False


# =====================================================
# REGISTRY
# =====================================================

_ACTIVE: Dict[int, OTPRecord] = {}


# =====================================================
# COMM CHANNELS (STUBS)
# =====================================================

def send_sms(phone: str, message: str):
    print(f"[SMS] {phone}: {message}")


def send_whatsapp(phone: str, message: str):
    print(f"[WHATSAPP] {phone}: {message}")


# =====================================================
# OTP GENERATION
# =====================================================

def generate_otp(order_id, buyer_id, driver_id, ttl=600):

    code = str(secrets.randbelow(900000) + 100000)

    now = time.time()

    record = OTPRecord(
        order_id=order_id,
        buyer_id=buyer_id,
        driver_id=driver_id,
        code=code,
        created_at=now,
        expires_at=now + ttl,
    )

    _ACTIVE[order_id] = record

    return record


# =====================================================
# DISPATCH
# =====================================================

def dispatch_otp(record: OTPRecord, buyer_phone, driver_phone):

    msg = f"FlipTrybe Delivery Code: {record.code}. Expires in 10 minutes."

    send_sms(buyer_phone, msg)
    send_whatsapp(driver_phone, msg)


# =====================================================
# VALIDATION
# =====================================================

def verify_otp(order_id: int, submitted: str):

    record = _ACTIVE.get(order_id)

    if not record:
        return False, "OTP not found"

    if record.locked:
        return False, "Order locked due to repeated failures"

    now = time.time()

    if now > record.expires_at:
        return False, "OTP expired"

    record.attempts += 1

    if record.attempts > 4:
        record.locked = True
        return False, "Too many attempts. Order locked"

    if submitted != record.code:
        return False, "Invalid OTP"

    # success
    del _ACTIVE[order_id]

    return True, "Verified"


# =====================================================
# ESCROW HOOK
# =====================================================

def on_delivery_confirmed(order_id, release_func):

    """
    release_func: callable(order_id)
    """

    ok, msg = verify_otp(order_id, submitted="")  # placeholder

    if not ok:
        return False, msg

    release_func(order_id)

    return True, "Escrow released"


# =====================================================
# ADMIN OVERRIDE
# =====================================================

def force_unlock(order_id):

    record = _ACTIVE.get(order_id)

    if record:
        record.locked = False
        record.attempts = 0
        return True

    return False


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    otp = generate_otp(order_id=88, buyer_id=1, driver_id=2)

    dispatch_otp(otp, "+2348000000", "+2348111111")

    print(verify_otp(88, "123456"))
    print(verify_otp(88, otp.code))