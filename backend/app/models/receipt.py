from datetime import datetime

from app.extensions import db


class Receipt(db.Model):
    __tablename__ = "receipts"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    kind = db.Column(db.String(40), nullable=False)  # listing_sale | delivery | withdrawal | shortlet_booking | topup
    reference = db.Column(db.String(120), nullable=False)  # external ref / internal order id
    amount = db.Column(db.Float, nullable=False, default=0.0)
    fee = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)

    description = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    meta = db.Column(db.Text, nullable=True)  # JSON string

    def meta_dict(self):
        raw = (self.meta or "").strip()
        if not raw:
            return {}
        try:
            import json
            d = json.loads(raw)
            return d if isinstance(d, dict) else {}
        except Exception:
            return {}

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "kind": self.kind or "",
            "reference": self.reference or "",
            "amount": float(self.amount or 0.0),
            "fee": float(self.fee or 0.0),
            "total": float(self.total or 0.0),
            "description": self.description or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "meta": self.meta_dict(),
        }
