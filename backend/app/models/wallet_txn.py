from datetime import datetime

from app.extensions import db


class WalletTxn(db.Model):
    __tablename__ = "wallet_txns"

    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey("wallets.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    direction = db.Column(db.String(8), nullable=False)  # credit/debit
    amount = db.Column(db.Float, nullable=False, default=0.0)

    kind = db.Column(db.String(32), nullable=False, default="misc")  # order_sale, delivery_fee, commission_fee, payout
    reference = db.Column(db.String(80), nullable=True, index=True)
    idempotency_key = db.Column(db.String(160), nullable=True, unique=True, index=True)

    note = db.Column(db.String(240), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": int(self.id),
            "wallet_id": int(self.wallet_id),
            "user_id": int(self.user_id),
            "direction": self.direction,
            "amount": float(self.amount or 0.0),
            "kind": self.kind,
            "reference": self.reference or "",
            "note": self.note or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
