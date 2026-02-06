"""
=====================================================
FLIPTRYBE SEGMENT 63
NOTIFICATION DISPATCHER
=====================================================
Unified fanout system for
SMS, Email, In-App alerts.
Includes retries + dead letter queue.
=====================================================
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Callable
from datetime import datetime


# =====================================================
# DATA MODELS
# =====================================================

@dataclass
class Notification:
    id: str
    user_id: int
    channel: str
    destination: str
    title: str
    message: str
    attempts: int = 0
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DeadLetter:
    notification_id: str
    reason: str
    failed_at: datetime = field(default_factory=datetime.utcnow)


# =====================================================
# STORES (STUBS)
# =====================================================

QUEUE: List[Notification] = []
SENT: Dict[str, Notification] = {}
FAILED: Dict[str, DeadLetter] = {}

IDEMPOTENCY_KEYS: set = set()


# =====================================================
# PROVIDER ABSTRACTION
# =====================================================

class Provider:

    def send(self, notification: Notification) -> bool:
        raise NotImplementedError


class SMSProvider(Provider):

    def send(self, notification):
        print(f"📲 SMS → {notification.destination}: {notification.message}")
        return True


class EmailProvider(Provider):

    def send(self, notification):
        print(f"📧 EMAIL → {notification.destination}: {notification.title}")
        return True


class InAppProvider(Provider):

    def send(self, notification):
        print(f"🔔 IN APP → user {notification.user_id}: {notification.message}")
        return True


PROVIDERS: Dict[str, Provider] = {
    "sms": SMSProvider(),
    "email": EmailProvider(),
    "in_app": InAppProvider(),
}


# =====================================================
# QUEUE ENQUEUE
# =====================================================

def enqueue_notification(
    user_id: int,
    channel: str,
    destination: str,
    title: str,
    message: str,
    idempotency_key: str = None,
):

    if idempotency_key and idempotency_key in IDEMPOTENCY_KEYS:
        print("♻ Notification deduplicated")
        return

    notif = Notification(
        id=str(uuid.uuid4()),
        user_id=user_id,
        channel=channel,
        destination=destination,
        title=title,
        message=message,
    )

    QUEUE.append(notif)

    if idempotency_key:
        IDEMPOTENCY_KEYS.add(idempotency_key)


# =====================================================
# RETRY POLICY
# =====================================================

def backoff(attempt: int) -> int:
    return min(60, 2 ** attempt)


# =====================================================
# DISPATCH LOOP
# =====================================================

def process_queue():

    for notif in list(QUEUE):

        provider = PROVIDERS.get(notif.channel)

        if not provider:
            move_to_dead_letter(notif, "Unknown channel")
            continue

        success = provider.send(notif)

        if success:
            notif.status = "sent"
            SENT[notif.id] = notif
            QUEUE.remove(notif)
            continue

        notif.attempts += 1

        if notif.attempts >= 5:
            move_to_dead_letter(notif, "Retry limit exceeded")
        else:
            delay = backoff(notif.attempts)
            print(f"⏳ Retry in {delay}s")
            time.sleep(delay)


# =====================================================
# DEAD LETTER QUEUE
# =====================================================

def move_to_dead_letter(notification: Notification, reason: str):

    FAILED[notification.id] = DeadLetter(
        notification_id=notification.id,
        reason=reason
    )

    notification.status = "dead"
    if notification in QUEUE:
        QUEUE.remove(notification)

    print(f"☠ Notification dead lettered: {reason}")


# =====================================================
# AUDIT LOGGING
# =====================================================

def audit_snapshot():

    return {
        "queued": len(QUEUE),
        "sent": len(SENT),
        "failed": len(FAILED),
        "timestamp": datetime.utcnow().isoformat()
    }


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    enqueue_notification(
        user_id=1,
        channel="sms",
        destination="+2348012345678",
        title="Order Update",
        message="Your order is on the way 🚚",
        idempotency_key="ord-55-sms"
    )

    enqueue_notification(
        user_id=1,
        channel="email",
        destination="user@test.com",
        title="Payment Received",
        message="Escrow funded successfully"
    )

    process_queue()

    print(audit_snapshot())