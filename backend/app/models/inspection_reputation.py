from __future__ import annotations

from datetime import datetime

from app.extensions import db


class InspectorProfile(db.Model):
    """Inspector Agent profile + reputation.

    NOTE: We attach this to User via user_id. The user.role should be 'inspector'
    for operational correctness, but we do not hard-enforce role here to keep
    migrations safe.
    """

    __tablename__ = "inspector_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(32), nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    region = db.Column(db.String(64), nullable=True, index=True)

    completed_inspections = db.Column(db.Integer, nullable=False, default=0)
    failed_inspections = db.Column(db.Integer, nullable=False, default=0)
    fraud_flags = db.Column(db.Integer, nullable=False, default=0)

    dispute_overturned_count = db.Column(db.Integer, nullable=False, default=0)
    dispute_audit_count = db.Column(db.Integer, nullable=False, default=0)

    avg_turnaround_minutes = db.Column(db.Float, nullable=False, default=0.0)
    reputation_score = db.Column(db.Float, nullable=False, default=70.0, index=True)
    reputation_tier = db.Column(db.String(16), nullable=False, default="SILVER", index=True)

    last_score_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": int(self.id),
            "user_id": int(self.user_id),
            "phone": self.phone or "",
            "is_active": bool(self.is_active),
            "region": self.region or "",
            "completed_inspections": int(self.completed_inspections or 0),
            "failed_inspections": int(self.failed_inspections or 0),
            "fraud_flags": int(self.fraud_flags or 0),
            "dispute_overturned_count": int(self.dispute_overturned_count or 0),
            "dispute_audit_count": int(self.dispute_audit_count or 0),
            "avg_turnaround_minutes": float(self.avg_turnaround_minutes or 0.0),
            "reputation_score": float(self.reputation_score or 0.0),
            "reputation_tier": self.reputation_tier,
            "last_score_at": self.last_score_at.isoformat() if self.last_score_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class InspectionReview(db.Model):
    __tablename__ = "inspection_reviews"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    inspector_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    reviewer_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    rating = db.Column(db.Integer, nullable=False, default=5)
    tags_json = db.Column(db.Text, nullable=True)  # JSON array string
    comment = db.Column(db.String(400), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": int(self.id),
            "order_id": int(self.order_id),
            "inspector_user_id": int(self.inspector_user_id),
            "reviewer_user_id": int(self.reviewer_user_id),
            "rating": int(self.rating or 0),
            "tags": self.tags_json or "[]",
            "comment": self.comment or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class InspectionAudit(db.Model):
    __tablename__ = "inspection_audits"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    inspector_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    admin_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    decision = db.Column(db.String(16), nullable=False, default="UPHELD", index=True)
    reason = db.Column(db.String(400), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": int(self.id),
            "order_id": int(self.order_id),
            "inspector_user_id": int(self.inspector_user_id),
            "admin_user_id": int(self.admin_user_id),
            "decision": self.decision,
            "reason": self.reason or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
