from datetime import datetime

from app.extensions import db


class PaymentTransaction(db.Model):
    __tablename__ = "payment_transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)

    provider = db.Column(db.String(32), nullable=False, default="SIM")
    reference = db.Column(db.String(128), nullable=False, unique=True)

    amount = db.Column(db.Float, nullable=False, default=0.0)
    currency = db.Column(db.String(8), nullable=False, default="NGN")

    purpose = db.Column(db.String(32), nullable=False, default="topup")  # topup/order
    status = db.Column(db.String(32), nullable=False, default="initialized")  # initialized/paid/failed

    meta = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": int(self.id),
            "user_id": int(self.user_id),
            "provider": self.provider,
            "reference": self.reference,
            "amount": float(self.amount or 0.0),
            "currency": self.currency,
            "purpose": self.purpose,
            "status": self.status,
            "meta": self.meta or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
