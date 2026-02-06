"""
=====================================================
FLIPTRYBE SEGMENT 93
INCIDENT & FORENSICS ENGINE
=====================================================

Purpose:
Creates immutable-ish records for:

1. System incidents
2. Autonomic actions
3. Risk escalations
4. Freeze events
5. Kill-switch activations
6. Payment halts
7. Data anomalies
8. SLA breaches
9. Region failures
10. Security alerts
11. Compliance triggers
12. Admin overrides
13. Recovery events
14. Post-mortem summaries
15. Timeline reconstruction
=====================================================
"""

from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime
import uuid
import json


# =====================================================
# DATA MODELS
# =====================================================

@dataclass
class IncidentEvent:
    id: str
    type: str
    title: str
    details: Dict
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class IncidentRecord:
    id: str
    severity: str
    status: str
    opened_at: datetime
    closed_at: datetime | None = None
    events: List[IncidentEvent] = field(default_factory=list)
    summary: str | None = None


INCIDENTS: Dict[str, IncidentRecord] = {}


# =====================================================
# CORE OPS
# =====================================================

def open_incident(title, severity="medium"):

    iid = uuid.uuid4().hex

    INCIDENTS[iid] = IncidentRecord(
        id=iid,
        severity=severity,
        status="open",
        opened_at=datetime.utcnow(),
    )

    return iid


def add_event(incident_id, type_, title, details):

    inc = INCIDENTS.get(incident_id)

    if not inc:
        raise KeyError("Incident not found")

    inc.events.append(
        IncidentEvent(
            id=uuid.uuid4().hex,
            type=type_,
            title=title,
            details=details,
        )
    )


def close_incident(incident_id, summary):

    inc = INCIDENTS.get(incident_id)

    if not inc:
        raise KeyError("Incident not found")

    inc.status = "closed"
    inc.closed_at = datetime.utcnow()
    inc.summary = summary


# =====================================================
# FORENSIC EXPORT
# =====================================================

def export_incident(incident_id):

    inc = INCIDENTS.get(incident_id)

    if not inc:
        raise KeyError("Incident not found")

    return json.dumps(
        inc,
        default=lambda o: o.__dict__,
        indent=2,
    )


def timeline(incident_id):

    inc = INCIDENTS.get(incident_id)

    return sorted(
        inc.events,
        key=lambda e: e.created_at
    )


# =====================================================
# SUMMARY GENERATOR (HEURISTIC)
# =====================================================

def generate_summary(incident_id):

    inc = INCIDENTS.get(incident_id)

    lines = [
        f"Incident {inc.id} closed with {len(inc.events)} events."
    ]

    for e in inc.events:
        lines.append(f"- {e.type}: {e.title}")

    return "\n".join(lines)