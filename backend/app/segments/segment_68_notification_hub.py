"""
=====================================================
FLIPTRYBE SEGMENT 68
NOTIFICATION & MESSAGING ORCHESTRATOR
=====================================================
Responsibilities:
1. SMS engine (Termii-ready)
2. Email sender abstraction
3. Push fanout stub
4. Retry queue
5. Dead-letter store
6. Template engine
7. Metrics collector
8. Escalation rules
9. Batch dispatcher
10. Webhook sinks
=====================================================
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List
import uuid
import time


# =====================================================
# MODELS
# =====================================================

@dataclass
class Message:
    id: str
    user_id: int
    channel: str
    destination: str
    template: str
    payload: dict
    status: str = "queued"
    attempts: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DeliveryMetric:
    channel: str
    sent: int = 0
    failed: int = 0


# =====================================================
# STORES
# =====================================================

QUEUE: Dict[str, Message] = {}
DEAD_LETTERS: Dict[str, Message] = {}
METRICS: Dict[str, DeliveryMetric] = {}


# =====================================================
# TEMPLATE ENGINE
# =====================================================

TEMPLATES = {
    "otp": "Your FlipTrybe code is {code}",
    "order_update": "Order #{order_id} status: {status}",
    "payout": "Payout of {amount} processed",
}


def render_template(name: str, payload: dict):

    template = TEMPLATES.get(name, "")

    return template.format(**payload)


# =====================================================
# CHANNEL SENDERS
# =====================================================

def send_sms(number: str, body: str):
    # Stub for Termii integration
    print(f"[SMS] {number}: {body}")
    return True


def send_email(email: str, subject: str, body: str):
    print(f"[EMAIL] {email}: {subject} | {body}")
    return True


def send_push(device_id: str, body: str):
    print(f"[PUSH] {device_id}: {body}")
    return True


CHANNEL_MAP = {
    "sms": send_sms,
    "email": send_email,
    "push": send_push,
}


# =====================================================
# METRICS
# =====================================================

def _metric(channel: str, success: bool):

    m = METRICS.setdefault(channel, DeliveryMetric(channel=channel))

    if success:
        m.sent += 1
    else:
        m.failed += 1


# =====================================================
# DISPATCHER
# =====================================================

def dispatch_message(msg: Message):

    renderer = render_template(msg.template, msg.payload)

    sender = CHANNEL_MAP[msg.channel]

    try:
        if msg.channel == "email":
            ok = sender(msg.destination, "FlipTrybe", renderer)
        else:
            ok = sender(msg.destination, renderer)

        if ok:
            msg.status = "sent"
            _metric(msg.channel, True)
            return True

    except Exception:
        pass

    msg.attempts += 1

    if msg.attempts >= 3:
        msg.status = "dead"
        DEAD_LETTERS[msg.id] = msg
        _metric(msg.channel, False)
        return False

    msg.status = "retrying"
    return False


# =====================================================
# FANOUT
# =====================================================

def enqueue_message(
    user_id: int,
    channel: str,
    destination: str,
    template: str,
    payload: dict,
):

    mid = str(uuid.uuid4())

    msg = Message(
        id=mid,
        user_id=user_id,
        channel=channel,
        destination=destination,
        template=template,
        payload=payload,
    )

    QUEUE[mid] = msg
    return msg


# =====================================================
# BATCH PROCESSOR
# =====================================================

def process_queue(batch_size=25):

    batch = list(QUEUE.values())[:batch_size]

    for msg in batch:

        dispatch_message(msg)

        if msg.status == "sent":
            QUEUE.pop(msg.id, None)


# =====================================================
# ESCALATION RULES
# =====================================================

def escalate_dead_letters():

    for msg in DEAD_LETTERS.values():
        print(f"[ESCALATE] {msg.channel} -> {msg.destination}")


# =====================================================
# WEBHOOK SINK
# =====================================================

def ingest_webhook(payload: dict):

    event = payload.get("event")

    print(f"[WEBHOOK INGEST] {event}")


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    enqueue_message(
        user_id=9,
        channel="sms",
        destination="+2348012345678",
        template="otp",
        payload={"code": "332211"},
    )

    enqueue_message(
        user_id=9,
        channel="email",
        destination="test@fliptrybe.com",
        template="order_update",
        payload={"order_id": 44, "status": "Delivered"},
    )

    process_queue()

    print("METRICS:", METRICS)