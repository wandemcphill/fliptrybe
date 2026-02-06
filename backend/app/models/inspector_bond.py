from datetime import datetime

from app.extensions import db


class InspectorBond(db.Model):
    __tablename__ = "inspector_bonds"

    id = db.Column(db.Integer, primary_key=True)
    inspector_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True)

    bond_currency = db.Column(db.String(8), nullable=False, default="NGN")
    bond_required_amount = db.Column(db.Float, nullable=False, default=0.0)
    bond_available_amount = db.Column(db.Float, nullable=False, default=0.0)
    bond_reserved_amount = db.Column(db.Float, nullable=False, default=0.0)

    status = db.Column(db.String(16), nullable=False, default="UNDERFUNDED")

    last_topup_at = db.Column(db.DateTime, nullable=True)
    last_slash_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": int(self.id),
            "inspector_user_id": int(self.inspector_user_id),
            "bond_currency": self.bond_currency or "NGN",
            "bond_required_amount": float(self.bond_required_amount or 0.0),
            "bond_available_amount": float(self.bond_available_amount or 0.0),
            "bond_reserved_amount": float(self.bond_reserved_amount or 0.0),
            "status": self.status or "UNDERFUNDED",
            "last_topup_at": self.last_topup_at.isoformat() if self.last_topup_at else None,
            "last_slash_at": self.last_slash_at.isoformat() if self.last_slash_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class BondEvent(db.Model):
    __tablename__ = "bond_events"

    id = db.Column(db.Integer, primary_key=True)
    inspector_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    event_type = db.Column(db.String(24), nullable=False, default="TOPUP")
    amount = db.Column(db.Float, nullable=False, default=0.0)

    reference_type = db.Column(db.String(24), nullable=True)
    reference_id = db.Column(db.Integer, nullable=True)

    note = db.Column(db.String(400), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": int(self.id),
            "inspector_user_id": int(self.inspector_user_id),
            "event_type": self.event_type,
            "amount": float(self.amount or 0.0),
            "reference_type": self.reference_type or "",
            "reference_id": int(self.reference_id) if self.reference_id is not None else None,
            "note": self.note or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
