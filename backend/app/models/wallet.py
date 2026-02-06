from datetime import datetime

from app.extensions import db


class Wallet(db.Model):
    __tablename__ = "wallets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True, index=True)

    balance = db.Column(db.Float, nullable=False, default=0.0)

    reserved_balance = db.Column(db.Float, nullable=False, default=0.0)
    currency = db.Column(db.String(8), nullable=False, default="NGN")

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "user_id": int(self.user_id),
            "balance": float(self.balance or 0.0),
            "reserved_balance": float(self.reserved_balance or 0.0),
            "available_balance": float((self.balance or 0.0) - (self.reserved_balance or 0.0)),
            "currency": self.currency or "NGN",
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
