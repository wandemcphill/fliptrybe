from __future__ import annotations

import random
import string


def simulate_transfer(bank_name: str, account_number: str, amount: float) -> dict:
    """Simulates an external transfer. Replace with Paystack/Flutterwave later."""
    ref = "TRX_" + "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    return {
        "ok": True,
        "provider": "simulated",
        "reference": ref,
        "bank_name": bank_name,
        "account_number": account_number,
        "amount": amount,
        "status": "success",
    }
