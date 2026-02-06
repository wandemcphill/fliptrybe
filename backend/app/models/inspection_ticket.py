from datetime import datetime

from app.extensions import db


class InspectionTicket(db.Model):
    __tablename__ = "inspection_tickets"
    __table_args__ = (
        db.UniqueConstraint("order_id", name="uq_inspection_ticket_order"),
    )

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    inspector_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    seller_phone = db.Column(db.String(32), nullable=True)
    seller_address = db.Column(db.String(200), nullable=True)
    item_summary = db.Column(db.String(200), nullable=True)

    buyer_full_name = db.Column(db.String(120), nullable=True)
    buyer_phone = db.Column(db.String(32), nullable=True)

    scheduled_for = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(16), nullable=False, default="created")

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": int(self.id),
            "order_id": int(self.order_id),
            "inspector_id": int(self.inspector_id) if self.inspector_id else None,
            "seller_phone": self.seller_phone or "",
            "seller_address": self.seller_address or "",
            "item_summary": self.item_summary or "",
            "buyer_full_name": self.buyer_full_name or "",
            "buyer_phone": self.buyer_phone or "",
            "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "status": self.status or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
