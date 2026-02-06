"""
=====================================================
FLIPTRYBE SEGMENT 66
KYC & IDENTITY VERIFICATION ENGINE
=====================================================
Responsibilities:
1. Document submission intake
2. OCR extraction stub
3. Identity scoring
4. Fraud screening
5. Watchlists
6. Tier promotion
7. Expiry monitoring
8. Audit trails
9. Manual review queue
10. Webhook emission
=====================================================
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid


# =====================================================
# MODELS
# =====================================================

@dataclass
class KYCDocument:
    id: str
    user_id: int
    doc_type: str
    country: str
    number: str
    expiry_date: datetime
    image_path: str
    extracted_name: Optional[str] = None
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class KYCProfile:
    user_id: int
    tier: str = "Unverified"
    risk_score: float = 0.0
    last_reviewed: Optional[datetime] = None


@dataclass
class AuditLog:
    id: str
    user_id: int
    action: str
    detail: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ManualReviewTicket:
    id: str
    user_id: int
    reason: str
    opened_at: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False


# =====================================================
# STORES
# =====================================================

DOCUMENTS: Dict[str, KYCDocument] = {}
PROFILES: Dict[int, KYCProfile] = {}
AUDIT_LOGS: List[AuditLog] = []
MANUAL_QUEUE: Dict[str, ManualReviewTicket] = {}

WATCHLIST = {
    "numbers": set(["X999999"]),
    "names": set(["JOHN DOE"]),
}


# =====================================================
# HELPERS
# =====================================================

def _audit(user_id: int, action: str, detail: str):
    AUDIT_LOGS.append(
        AuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            detail=detail,
        )
    )


def _emit_webhook(event: str, payload: dict):
    # Stub for webhook dispatch
    print(f"[WEBHOOK] {event}: {payload}")


# =====================================================
# OCR STUB
# =====================================================

def run_ocr(image_path: str):

    # Placeholder for OCR engine integration
    return {
        "name": "AUTO PARSED NAME",
        "number": "ID123456",
    }


# =====================================================
# SUBMISSION
# =====================================================

def submit_document(
    user_id: int,
    doc_type: str,
    country: str,
    number: str,
    expiry_date: datetime,
    image_path: str,
):

    doc_id = str(uuid.uuid4())

    ocr = run_ocr(image_path)

    doc = KYCDocument(
        id=doc_id,
        user_id=user_id,
        doc_type=doc_type,
        country=country,
        number=number,
        expiry_date=expiry_date,
        image_path=image_path,
        extracted_name=ocr.get("name"),
    )

    DOCUMENTS[doc_id] = doc

    _audit(user_id, "doc_submitted", doc_type)

    evaluate_document(doc)

    return doc


# =====================================================
# FRAUD + SCORING
# =====================================================

def compute_risk_score(user_id: int):

    score = 0.0

    docs = [d for d in DOCUMENTS.values() if d.user_id == user_id]

    for d in docs:
        if d.number in WATCHLIST["numbers"]:
            score += 0.6
        if d.extracted_name in WATCHLIST["names"]:
            score += 0.6

        if d.expiry_date < datetime.utcnow():
            score += 0.4

    return min(score, 1.0)


def evaluate_document(doc: KYCDocument):

    risk = compute_risk_score(doc.user_id)

    profile = PROFILES.setdefault(
        doc.user_id,
        KYCProfile(user_id=doc.user_id),
    )

    profile.risk_score = risk

    if risk > 0.7:
        doc.status = "flagged"
        open_manual_review(doc.user_id, "High risk KYC")
        _emit_webhook("kyc.flagged", {"user_id": doc.user_id})
        return

    doc.status = "approved"
    promote_tier(profile)

    _audit(doc.user_id, "doc_verified", doc.doc_type)
    _emit_webhook("kyc.approved", {"user_id": doc.user_id})


# =====================================================
# MANUAL REVIEW
# =====================================================

def open_manual_review(user_id: int, reason: str):

    tid = str(uuid.uuid4())

    MANUAL_QUEUE[tid] = ManualReviewTicket(
        id=tid,
        user_id=user_id,
        reason=reason,
    )

    _audit(user_id, "manual_review_opened", reason)


def resolve_manual_review(ticket_id: str, approve: bool):

    ticket = MANUAL_QUEUE.get(ticket_id)

    if not ticket:
        raise ValueError("Ticket not found")

    ticket.resolved = True

    profile = PROFILES.setdefault(
        ticket.user_id,
        KYCProfile(user_id=ticket.user_id),
    )

    if approve:
        promote_tier(profile)
        _emit_webhook("kyc.manual_approved", {"user_id": ticket.user_id})
    else:
        profile.tier = "Rejected"
        _emit_webhook("kyc.manual_rejected", {"user_id": ticket.user_id})

    _audit(ticket.user_id, "manual_review_closed", str(approve))


# =====================================================
# TIER ENGINE
# =====================================================

def promote_tier(profile: KYCProfile):

    if profile.risk_score > 0.5:
        return

    if profile.tier == "Unverified":
        profile.tier = "Tier1"
    elif profile.tier == "Tier1":
        profile.tier = "Tier2"
    elif profile.tier == "Tier2":
        profile.tier = "Tier3"

    profile.last_reviewed = datetime.utcnow()


# =====================================================
# EXPIRY MONITOR
# =====================================================

def scan_expiring_documents(days=30):

    cutoff = datetime.utcnow() + timedelta(days=days)

    expiring = [
        d for d in DOCUMENTS.values()
        if d.expiry_date <= cutoff and d.status == "approved"
    ]

    for d in expiring:
        _emit_webhook("kyc.expiring", {
            "user_id": d.user_id,
            "doc_id": d.id,
        })


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    doc = submit_document(
        user_id=5,
        doc_type="passport",
        country="NG",
        number="A12345",
        expiry_date=datetime.utcnow() + timedelta(days=400),
        image_path="uploads/passport.png",
    )

    print(doc)

    scan_expiring_documents()