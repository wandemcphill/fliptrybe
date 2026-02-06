from datetime import datetime

from app.extensions import db


class EscrowUnlock(db.Model):
    __tablename__ = "escrow_unlocks"
    __table_args__ = (
        db.UniqueConstraint("order_id", "step", name="uq_escrow_unlock_order_step"),
    )

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    step = db.Column(db.String(32), nullable=False, index=True)

    code_hash = db.Column(db.String(128), nullable=True)

    attempts = db.Column(db.Integer, nullable=False, default=0)
    max_attempts = db.Column(db.Integer, nullable=False, default=4)
    locked = db.Column(db.Boolean, nullable=False, default=False)

    qr_required = db.Column(db.Boolean, nullable=False, default=True)
    qr_verified = db.Column(db.Boolean, nullable=False, default=False)
    qr_verified_at = db.Column(db.DateTime, nullable=True)

    unlocked_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

    admin_unlock_token_hash = db.Column(db.String(128), nullable=True)
    admin_unlock_expires_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": int(self.id),
            "order_id": int(self.order_id),
            "step": self.step or "",
            "attempts": int(self.attempts or 0),
            "max_attempts": int(self.max_attempts or 0),
            "locked": bool(self.locked),
            "qr_required": bool(self.qr_required),
            "qr_verified": bool(self.qr_verified),
            "qr_verified_at": self.qr_verified_at.isoformat() if self.qr_verified_at else None,
            "unlocked_at": self.unlocked_at.isoformat() if self.unlocked_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
