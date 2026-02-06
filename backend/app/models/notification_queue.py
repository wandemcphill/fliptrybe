from datetime import datetime, timedelta

from app.extensions import db


class NotificationQueue(db.Model):
    __tablename__ = "notification_queue"

    id = db.Column(db.Integer, primary_key=True)
    channel = db.Column(db.String(32), nullable=False)
    to = db.Column(db.String(128), nullable=False)
    message = db.Column(db.Text, nullable=False)

    # queued -> sent / failed / dead
    status = db.Column(db.String(32), nullable=False, default="queued")
    reference = db.Column(db.String(128), nullable=True)

    # Reliability fields
    attempt_count = db.Column(db.Integer, nullable=False, default=0)
    max_attempts = db.Column(db.Integer, nullable=False, default=5)
    next_attempt_at = db.Column(db.DateTime, nullable=True)
    last_error = db.Column(db.String(240), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime, nullable=True)
    dead_lettered_at = db.Column(db.DateTime, nullable=True)

    def schedule_next_attempt(self, *, base_seconds: int = 15, max_seconds: int = 3600):
        """Exponential backoff with a cap."""
        try:
            n = int(self.attempt_count or 0)
        except Exception:
            n = 0
        delay = min(int(base_seconds * (2 ** max(n, 0))), int(max_seconds))
        self.next_attempt_at = datetime.utcnow() + timedelta(seconds=delay)

    def to_dict(self):
        return {
            "id": int(self.id),
            "channel": self.channel,
            "to": self.to,
            "message": self.message,
            "status": self.status,
            "reference": self.reference or "",
            "attempt_count": int(self.attempt_count or 0),
            "max_attempts": int(self.max_attempts or 0),
            "next_attempt_at": self.next_attempt_at.isoformat() if self.next_attempt_at else None,
            "last_error": self.last_error or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "dead_lettered_at": self.dead_lettered_at.isoformat() if self.dead_lettered_at else None,
        }
