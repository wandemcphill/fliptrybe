from datetime import datetime, timedelta

from app.extensions import db


class AvailabilityConfirmation(db.Model):
    __tablename__ = "availability_confirmations"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, unique=True, index=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id"), nullable=True, index=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    status = db.Column(db.String(16), nullable=False, default="pending")  # pending | yes | no | expired
    requested_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    deadline_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(hours=2))
    responded_at = db.Column(db.DateTime, nullable=True)

    response_token = db.Column(db.String(96), nullable=False, unique=True, index=True)

    def to_dict(self):
        return {
            "order_id": int(self.order_id),
            "listing_id": int(self.listing_id) if self.listing_id is not None else None,
            "merchant_id": int(self.merchant_id) if self.merchant_id is not None else None,
            "seller_id": int(self.seller_id) if self.seller_id is not None else None,
            "status": self.status,
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "deadline_at": self.deadline_at.isoformat() if self.deadline_at else None,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
        }
