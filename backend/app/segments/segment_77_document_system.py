"""
=====================================================
FLIPTRYBE SEGMENT 77
DOCUMENT & RECORD MANAGEMENT CORE
=====================================================
Responsibilities:
1. Upload handling
2. OCR ingestion stub
3. Search indexing
4. Versioning
5. Access control
6. Audit trails
7. Lifecycle automation
8. Retention rules
9. Exports
10. Archival
=====================================================
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List
import uuid
import csv
import io


# =====================================================
# MODELS
# =====================================================

@dataclass
class Document:
    id: str
    name: str
    owner_id: int
    version: int
    content: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AuditTrail:
    id: str
    actor: int
    action: str
    document_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


# =====================================================
# STORES
# =====================================================

DOCUMENTS: Dict[str, List[Document]] = {}
INDEX: Dict[str, List[str]] = {}
AUDITS: List[AuditTrail] = {}
ARCHIVE: Dict[str, Document] = {}


# =====================================================
# UPLOAD
# =====================================================

def upload_document(owner_id: int, name: str, content: str):

    did = str(uuid.uuid4())

    doc = Document(
        id=did,
        name=name,
        owner_id=owner_id,
        version=1,
        content=content,
    )

    DOCUMENTS.setdefault(name, []).append(doc)

    index_document(doc)

    return doc


# =====================================================
# OCR (STUB)
# =====================================================

def run_ocr(blob: bytes):

    # Placeholder for OCR engine
    return blob.decode(errors="ignore")


# =====================================================
# INDEXING
# =====================================================

def index_document(doc: Document):

    for token in doc.content.lower().split():

        INDEX.setdefault(token, []).append(doc.id)


def search(query: str):

    return INDEX.get(query.lower(), [])


# =====================================================
# VERSIONING
# =====================================================

def new_version(name: str, content: str):

    history = DOCUMENTS[name]

    v = len(history) + 1

    doc = Document(
        id=str(uuid.uuid4()),
        name=name,
        owner_id=history[0].owner_id,
        version=v,
        content=content,
    )

    history.append(doc)

    index_document(doc)

    return doc


# =====================================================
# ACCESS CONTROL
# =====================================================

ACL: Dict[str, List[int]] = {}


def grant_access(doc_name: str, user_id: int):

    ACL.setdefault(doc_name, []).append(user_id)


def can_access(doc_name: str, user_id: int):

    return user_id in ACL.get(doc_name, [])


# =====================================================
# AUDIT
# =====================================================

def audit(actor, action, doc_id):

    AUDITS.append(
        AuditTrail(
            id=str(uuid.uuid4()),
            actor=actor,
            action=action,
            document_id=doc_id,
        )
    )


# =====================================================
# LIFECYCLE
# =====================================================

def expire_documents(days=365):

    cutoff = datetime.utcnow() - timedelta(days=days)

    expired = []

    for docs in DOCUMENTS.values():
        for d in docs:
            if d.created_at < cutoff:
                expired.append(d)

    return expired


# =====================================================
# ARCHIVAL
# =====================================================

def archive_document(doc_id):

    for docs in DOCUMENTS.values():
        for d in docs:
            if d.id == doc_id:
                ARCHIVE[doc_id] = d
                return d


# =====================================================
# EXPORT
# =====================================================

def export_documents_csv():

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow(["id", "name", "version", "owner"])

    for docs in DOCUMENTS.values():
        for d in docs:
            writer.writerow([d.id, d.name, d.version, d.owner_id])

    return output.getvalue()


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    d = upload_document(3, "kyc.txt", "passport id nigeria")

    grant_access("kyc.txt", 7)

    print("SEARCH passport:", search("passport"))

    d2 = new_version("kyc.txt", "passport id nigeria verified")

    print("VERSIONS:", DOCUMENTS["kyc.txt"])

    print("EXPORT:\n", export_documents_csv())