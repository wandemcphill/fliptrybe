from datetime import datetime

from app.extensions import db


class PayoutRequest(db.Model):
    __tablename__ = "payout_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    amount = db.Column(db.Float, nullable=False, default=0.0)
    fee_amount = db.Column(db.Float, nullable=False, default=0.0)
    net_amount = db.Column(db.Float, nullable=False, default=0.0)
    speed = db.Column(db.String(16), nullable=False, default="standard")
    status = db.Column(db.String(24), nullable=False, default="pending")  # pending/approved/paid/rejected

    bank_name = db.Column(db.String(80), nullable=True)
    account_number = db.Column(db.String(32), nullable=True)
    account_name = db.Column(db.String(120), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": int(self.id),
            "user_id": int(self.user_id),
            "amount": float(self.amount or 0.0),
            "fee_amount": float(self.fee_amount or 0.0),
            "net_amount": float(self.net_amount or 0.0),
            "speed": (self.speed or "standard"),
            "status": self.status,
            "bank_name": self.bank_name or "",
            "account_number": self.account_number or "",
            "account_name": self.account_name or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
