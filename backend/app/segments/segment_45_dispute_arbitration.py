"""
=====================================================
FLIPTRYBE SEGMENT 45
DISPUTE ARBITRATION & ESCROW COURT
=====================================================
Analyzes delivery logs, OTP attempts, GPS traces,
and transaction history to produce automated rulings.
=====================================================
"""

import time
import uuid
from pathlib import Path
from typing import Dict, List

from app.segments.segment_44_compliance_engine import append_ledger
from app.segments.segment_43_telemetry_and_slo import audit


ROOT = Path.cwd()

CASEBOOK = ROOT / "dispute_cases.json"


# =====================================================
# STORAGE
# =====================================================

def load_cases():
    if CASEBOOK.exists():
        import json
        return json.loads(CASEBOOK.read_text())
    return {}


def save_cases(cases):
    import json
    CASEBOOK.write_text(json.dumps(cases, indent=2))


# =====================================================
# EVIDENCE GRAPH
# =====================================================

def build_evidence(order_id: int):

    # In merged build these pull from DB tables:
    # - otp_attempts
    # - delivery_tracks
    # - transactions
    # - notifications

    evidence = {
        "order_id": order_id,
        "gps_path": [],
        "otp_attempts": [],
        "messages": [],
        "payments": [],
    }

    return evidence


# =====================================================
# RULING ENGINE
# =====================================================

def arbitrate(order_id: int):

    cases = load_cases()

    case_id = str(uuid.uuid4())

    evidence = build_evidence(order_id)

    score = 0

    if not evidence["gps_path"]:
        score += 1

    if len(evidence["otp_attempts"]) >= 4:
        score += 2

    if not evidence["payments"]:
        score += 2

    ruling = "manual_review"

    if score <= 1:
        ruling = "release_escrow"

    elif score >= 4:
        ruling = "refund_buyer"

    case = {
        "case_id": case_id,
        "order_id": order_id,
        "score": score,
        "ruling": ruling,
        "evidence": evidence,
        "ts": time.time(),
    }

    cases[case_id] = case
    save_cases(cases)

    append_ledger("dispute_arbitrated", case)
    audit("dispute_case", case)

    return case


# =====================================================
# APPEALS
# =====================================================

def appeal(case_id: str, user_id: int, statement: str):

    cases = load_cases()

    case = cases.get(case_id)
    if not case:
        raise ValueError("Case not found")

    case.setdefault("appeals", []).append(
        {
            "user_id": user_id,
            "statement": statement,
            "ts": time.time(),
        }
    )

    save_cases(cases)

    append_ledger(
        "dispute_appealed",
        {"case_id": case_id, "user_id": user_id},
    )

    return case


# =====================================================
# ADMIN OVERRIDE
# =====================================================

def admin_override(case_id: str, new_ruling: str, officer: str):

    cases = load_cases()

    case = cases.get(case_id)
    if not case:
        raise ValueError("Case not found")

    case["ruling"] = new_ruling
    case["overridden_by"] = officer
    case["override_ts"] = time.time()

    save_cases(cases)

    append_ledger(
        "dispute_override",
        {
            "case_id": case_id,
            "officer": officer,
            "ruling": new_ruling,
        },
    )

    return case


# =====================================================
# STANDALONE TEST
# =====================================================

if __name__ == "__main__":

    print("⚖️ Dispute court online")

    result = arbitrate(77)
    print(result)

    appeal(result["case_id"], 42, "Item damaged on arrival")

    admin_override(result["case_id"], "refund_buyer", "chief_officer")