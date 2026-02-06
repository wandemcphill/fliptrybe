"""
=====================================================
FLIPTRYBE SEGMENT 73
LEGAL & GOVERNANCE CONTROL PLANE
=====================================================
Responsibilities:
1. Jurisdiction rule engine
2. Age verification gates
3. Consent logs
4. Policy diffs
5. Takedown pipelines
6. Regulator exports
7. Subpoena intake
8. Enforcement queues
9. Geo compliance
10. Reporting
=====================================================
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import uuid
import csv
import io


# =====================================================
# JURISDICTION RULES
# =====================================================

RULES = {
    "NG": {"min_age": 18, "adult_content": False},
    "EU": {"min_age": 18, "adult_content": False},
    "US": {"min_age": 18, "adult_content": False},
}


def check_jurisdiction(country: str, age: int):

    rule = RULES.get(country, {"min_age": 18})

    return age >= rule["min_age"]


# =====================================================
# CONSENT LOGS
# =====================================================

@dataclass
class ConsentLog:
    id: str
    user_id: int
    policy_version: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


CONSENTS: Dict[str, ConsentLog] = {}


def record_consent(user_id: int, policy_version: str):

    cid = str(uuid.uuid4())

    CONSENTS[cid] = ConsentLog(
        id=cid,
        user_id=user_id,
        policy_version=policy_version,
    )

    return CONSENTS[cid]


# =====================================================
# POLICY DIFF
# =====================================================

POLICIES: Dict[str, str] = {}


def store_policy(version: str, text: str):

    POLICIES[version] = text


def diff_policies(old: str, new: str):

    o = POLICIES.get(old, "")
    n = POLICIES.get(new, "")

    return {
        "old": old,
        "new": new,
        "changed": o != n,
    }


# =====================================================
# TAKEDOWNS
# =====================================================

@dataclass
class TakedownRequest:
    id: str
    resource: str
    reason: str
    status: str = "open"
    created_at: datetime = field(default_factory=datetime.utcnow)


TAKEDOWNS: Dict[str, TakedownRequest] = {}


def request_takedown(resource: str, reason: str):

    tid = str(uuid.uuid4())

    TAKEDOWNS[tid] = TakedownRequest(
        id=tid,
        resource=resource,
        reason=reason,
    )

    return TAKEDOWNS[tid]


def resolve_takedown(tid: str, approve: bool):

    td = TAKEDOWNS.get(tid)

    if not td:
        raise ValueError("Takedown not found")

    td.status = "approved" if approve else "rejected"
    return td


# =====================================================
# SUBPOENAS
# =====================================================

@dataclass
class Subpoena:
    id: str
    authority: str
    user_id: int
    scope: str
    received_at: datetime = field(default_factory=datetime.utcnow)


SUBPOENAS: Dict[str, Subpoena] = {}


def ingest_subpoena(authority: str, user_id: int, scope: str):

    sid = str(uuid.uuid4())

    SUBPOENAS[sid] = Subpoena(
        id=sid,
        authority=authority,
        user_id=user_id,
        scope=scope,
    )

    return SUBPOENAS[sid]


# =====================================================
# ENFORCEMENT QUEUE
# =====================================================

ENFORCEMENT: Dict[str, str] = {}


def enqueue_enforcement(action: str):

    eid = str(uuid.uuid4())

    ENFORCEMENT[eid] = action
    return eid


# =====================================================
# REPORTING
# =====================================================

def export_regulator_csv():

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["id", "resource", "status"])

    for t in TAKEDOWNS.values():
        writer.writerow([t.id, t.resource, t.status])

    return output.getvalue()


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    store_policy("v1", "Initial")
    store_policy("v2", "Updated")

    print(diff_policies("v1", "v2"))

    c = record_consent(7, "v2")

    print("CONSENT:", c)

    td = request_takedown("listing:33", "copyright")

    print("TAKEDOWN:", td)

    print("REPORT CSV:\n", export_regulator_csv())