"""
=====================================================
FLIPTRYBE SEGMENT 44
COMPLIANCE ENGINE • KYC • AML • AUDIT VAULT
=====================================================
Implements regulatory workflows, suspicious activity
scanning, immutable audit records, and export packs.
=====================================================
"""

import time
import json
import uuid
import hashlib
from pathlib import Path
from typing import Dict, List

ROOT = Path.cwd()

VAULT_DIR = ROOT / "compliance_vault"
VAULT_DIR.mkdir(exist_ok=True)

KYC_FILE = VAULT_DIR / "kyc_records.json"
AML_FILE = VAULT_DIR / "aml_flags.json"
SAR_FILE = VAULT_DIR / "sar_reports.json"
IMMUTABLE_LOG = VAULT_DIR / "ledger.log"

AML_THRESHOLDS = {
    "large_tx": 500_000,
    "rapid_tx_count": 5,
    "rapid_window_sec": 900,
}


# =====================================================
# IMMUTABLE LEDGER
# =====================================================

def _hash_entry(entry: dict) -> str:
    payload = json.dumps(entry, sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def append_ledger(event: str, payload: dict):

    record = {
        "id": str(uuid.uuid4()),
        "ts": time.time(),
        "event": event,
        "payload": payload,
    }

    record["hash"] = _hash_entry(record)

    with open(IMMUTABLE_LOG, "a") as f:
        f.write(json.dumps(record) + "\n")


# =====================================================
# STORAGE HELPERS
# =====================================================

def _load(path: Path):
    if path.exists():
        return json.loads(path.read_text())
    return {}


def _save(path: Path, data):
    path.write_text(json.dumps(data, indent=2))


# =====================================================
# KYC ENGINE
# =====================================================

KYC_STATES = [
    "unsubmitted",
    "pending_review",
    "approved",
    "rejected",
    "expired",
]


def submit_kyc(user_id: int, document_bundle: Dict):

    records = _load(KYC_FILE)

    entry = {
        "user_id": user_id,
        "submitted_at": time.time(),
        "status": "pending_review",
        "documents": document_bundle,
    }

    records[str(user_id)] = entry
    _save(KYC_FILE, records)

    append_ledger("kyc_submitted", {"user_id": user_id})


def review_kyc(user_id: int, approve: bool, officer: str):

    records = _load(KYC_FILE)

    record = records.get(str(user_id))
    if not record:
        raise ValueError("No KYC submission")

    record["status"] = "approved" if approve else "rejected"
    record["reviewed_by"] = officer
    record["reviewed_at"] = time.time()

    records[str(user_id)] = record
    _save(KYC_FILE, records)

    append_ledger(
        "kyc_reviewed",
        {"user_id": user_id, "approved": approve, "officer": officer},
    )


# =====================================================
# AML ENGINE
# =====================================================

_TX_HISTORY: Dict[int, List[float]] = {}


def scan_transaction(user_id: int, amount: float):

    now = time.time()

    history = _TX_HISTORY.setdefault(user_id, [])
    history.append(now)

    history[:] = [t for t in history if t > now - AML_THRESHOLDS["rapid_window_sec"]]

    flagged = False
    reasons = []

    if amount >= AML_THRESHOLDS["large_tx"]:
        flagged = True
        reasons.append("large_transaction")

    if len(history) >= AML_THRESHOLDS["rapid_tx_count"]:
        flagged = True
        reasons.append("rapid_fire_transactions")

    if flagged:
        record_flag(user_id, amount, reasons)

    return flagged, reasons


def record_flag(user_id: int, amount: float, reasons: list):

    flags = _load(AML_FILE)

    entry = {
        "user_id": user_id,
        "amount": amount,
        "reasons": reasons,
        "ts": time.time(),
    }

    flags.setdefault(str(user_id), []).append(entry)
    _save(AML_FILE, flags)

    append_ledger("aml_flagged", entry)


# =====================================================
# SAR REPORTING
# =====================================================

def generate_sar(user_id: int, narrative: str):

    reports = _load(SAR_FILE)

    sar_id = str(uuid.uuid4())

    report = {
        "sar_id": sar_id,
        "user_id": user_id,
        "narrative": narrative,
        "created_at": time.time(),
    }

    reports[sar_id] = report
    _save(SAR_FILE, reports)

    append_ledger("sar_generated", report)

    return sar_id


# =====================================================
# REGULATOR EXPORT
# =====================================================

def export_regulatory_bundle():

    bundle = {
        "kyc": _load(KYC_FILE),
        "aml": _load(AML_FILE),
        "sar": _load(SAR_FILE),
        "ledger": IMMUTABLE_LOG.read_text().splitlines()
        if IMMUTABLE_LOG.exists()
        else [],
    }

    export_file = VAULT_DIR / f"regulatory_export_{int(time.time())}.json"
    export_file.write_text(json.dumps(bundle, indent=2))

    append_ledger("regulatory_export", {"file": export_file.name})

    return export_file


# =====================================================
# COMPLIANCE DASHBOARD SNAPSHOT
# =====================================================

def compliance_snapshot():

    return {
        "kyc_pending": sum(
            1
            for v in _load(KYC_FILE).values()
            if v["status"] == "pending_review"
        ),
        "aml_flagged_users": len(_load(AML_FILE)),
        "sar_count": len(_load(SAR_FILE)),
    }


# =====================================================
# STANDALONE TEST
# =====================================================

if __name__ == "__main__":

    print("🛡️ Compliance engine online")

    submit_kyc(42, {"passport": "hash123"})
    review_kyc(42, True, "officer_A")

    flagged, reasons = scan_transaction(42, 750_000)
    print("Flagged:", flagged, reasons)

    sar = generate_sar(42, "High velocity crypto liquidation")
    print("SAR:", sar)

    print("Snapshot:", compliance_snapshot())