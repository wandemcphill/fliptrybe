from datetime import datetime

from app.extensions import db


class CommissionRule(db.Model):
    __tablename__ = "commission_rules"

    id = db.Column(db.Integer, primary_key=True)

    # kind: listing_sale, delivery, withdrawal (or others)
    kind = db.Column(db.String(32), nullable=False, index=True)

    # Optional scoping
    state = db.Column(db.String(64), nullable=True, index=True)
    category = db.Column(db.String(64), nullable=True, index=True)

    # commission rate as fraction (0.05 = 5%)
    rate = db.Column(db.Float, nullable=False, default=0.0)

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": int(self.id),
            "kind": self.kind,
            "state": self.state or "",
            "category": self.category or "",
            "rate": float(self.rate or 0.0),
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
