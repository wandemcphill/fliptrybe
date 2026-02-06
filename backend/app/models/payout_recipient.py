from datetime import datetime

from app.extensions import db


class PayoutRecipient(db.Model):
    __tablename__ = "payout_recipients"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, unique=True)

    provider = db.Column(db.String(32), nullable=False, default="paystack")
    recipient_code = db.Column(db.String(128), nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": int(self.id),
            "user_id": int(self.user_id),
            "provider": self.provider,
            "recipient_code": self.recipient_code,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
