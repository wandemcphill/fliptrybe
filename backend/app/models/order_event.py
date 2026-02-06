from datetime import datetime

from app.extensions import db


class OrderEvent(db.Model):
    __tablename__ = "order_events"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    event = db.Column(db.String(64), nullable=False)
    note = db.Column(db.String(250), nullable=True)
    idempotency_key = db.Column(db.String(160), nullable=True, unique=True, index=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": int(self.id),
            "order_id": int(self.order_id),
            "actor_user_id": int(self.actor_user_id) if self.actor_user_id is not None else None,
            "event": self.event,
            "note": self.note or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
