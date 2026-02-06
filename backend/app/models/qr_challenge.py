from datetime import datetime

from app.extensions import db


class QRChallenge(db.Model):
    __tablename__ = "qr_challenges"
    __table_args__ = (
        db.UniqueConstraint("challenge_hash", name="uq_qr_challenge_hash"),
    )

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    step = db.Column(db.String(32), nullable=False, index=True)
    issued_to_role = db.Column(db.String(16), nullable=False)

    challenge_hash = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(16), nullable=False, default="issued")

    scanned_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    issued_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    scanned_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": int(self.id),
            "order_id": int(self.order_id),
            "step": self.step or "",
            "issued_to_role": self.issued_to_role or "",
            "status": self.status or "",
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "scanned_at": self.scanned_at.isoformat() if self.scanned_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
